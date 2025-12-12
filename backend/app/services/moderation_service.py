"""
C.O.V.E.R.T - Moderation Service
Business logic for moderation system
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta
import logging
import hashlib

from app.models.report import Report, ReportStatus
from app.models.moderator import Moderator
from app.models.moderation import Moderation
from app.services.ai import report_triager, credibility_scorer, anomaly_detector

logger = logging.getLogger(__name__)


class ModerationService:
    """Service for managing moderation workflow"""

    async def get_moderation_queue(
        self,
        db: AsyncSession,
        moderator_id: str,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Report], int]:
        """
        Get reports pending moderation with priority sorting

        Priority order:
        1. High risk reports first
        2. Oldest reports first
        3. Match moderator expertise
        """
        try:
            # Get moderator preferences
            moderator = await db.execute(
                select(Moderator).where(Moderator.id == moderator_id)
            )
            moderator = moderator.scalar_one_or_none()

            # Build base query - only reports that need moderation
            query = select(Report).where(
                and_(
                    Report.status == ReportStatus.PENDING,
                    Report.visibility != 0,  # Not private
                    Report.deleted_at.is_(None)
                )
            )

            # Apply filters
            if category:
                query = query.where(Report.category == category)

            if risk_level:
                query = query.where(Report.risk_level == risk_level)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            # Priority sorting with AI-enhanced prioritization
            # 1. Critical/High risk first (from AI assessment)
            # 2. High verification score (credible reports)
            # 3. Oldest first (FIFO)
            query = query.order_by(
                # Risk level priority
                func.case(
                    (Report.risk_level == 'critical', 1),
                    (Report.risk_level == 'high', 2),
                    (Report.risk_level == 'medium', 3),
                    else_=4
                ),
                # Credibility score (higher = more priority)
                Report.verification_score.desc().nullslast(),
                # Submission time (oldest first)
                Report.submission_timestamp.asc()
            )

            # Apply pagination
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            reports = list(result.scalars().all())

            return reports, total

        except Exception as e:
            logger.error(f"Failed to get moderation queue: {e}")
            return [], 0

    async def start_review(
        self,
        db: AsyncSession,
        report_id: str,
        moderator_id: str,
    ) -> Optional[Moderation]:
        """Start reviewing a report"""
        try:
            # Check if report exists and is pending
            report = await db.execute(
                select(Report).where(
                    and_(
                        Report.id == report_id,
                        Report.status == ReportStatus.PENDING
                    )
                )
            )
            report = report.scalar_one_or_none()

            if not report:
                logger.warning(f"Report {report_id} not found or not pending")
                return None

            # Update report status
            report.status = ReportStatus.UNDER_REVIEW

            # Create moderation record
            moderation = Moderation(
                report_id=report_id,
                moderator_id=moderator_id,
                action='review_started',
                created_at=datetime.utcnow(),
            )

            db.add(moderation)
            await db.commit()
            await db.refresh(moderation)

            logger.info(f"Started review for report {report_id} by moderator {moderator_id}")
            return moderation

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to start review: {e}")
            return None

    async def submit_decision(
        self,
        db: AsyncSession,
        report_id: str,
        moderator_id: str,
        decision: str,
        encrypted_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> Optional[Moderation]:
        """Submit moderation decision"""
        try:
            # Get report
            report = await db.execute(
                select(Report).where(Report.id == report_id)
            )
            report = report.scalar_one_or_none()

            if not report:
                logger.warning(f"Report {report_id} not found")
                return None

            # Update report status based on decision
            if decision == 'accept':
                report.status = ReportStatus.VERIFIED
            elif decision == 'reject':
                report.status = ReportStatus.REJECTED
            elif decision == 'need_info':
                report.status = ReportStatus.PENDING  # Back to pending
            elif decision == 'escalate':
                report.status = ReportStatus.UNDER_REVIEW  # Keep under review

            report.reviewed_at = datetime.utcnow()

            # Create moderation record
            action_map = {
                'accept': 'verified',
                'reject': 'rejected',
                'need_info': 'request_info',
                'escalate': 'escalated'
            }

            moderation = Moderation(
                report_id=report_id,
                moderator_id=moderator_id,
                action=action_map[decision],
                decision=decision,
                encrypted_notes=encrypted_notes,
                rejection_reason=rejection_reason,
                completed_at=datetime.utcnow(),
                time_spent_seconds=time_spent_seconds,
            )

            db.add(moderation)

            # Update moderator stats
            moderator = await db.execute(
                select(Moderator).where(Moderator.id == moderator_id)
            )
            moderator = moderator.scalar_one_or_none()

            if moderator:
                moderator.total_reviews += 1
                moderator.last_active_at = datetime.utcnow()

                # Update average review time
                if time_spent_seconds:
                    if moderator.average_review_time_seconds:
                        total_time = (moderator.average_review_time_seconds * (moderator.total_reviews - 1) +
                                    time_spent_seconds)
                        moderator.average_review_time_seconds = int(total_time / moderator.total_reviews)
                    else:
                        moderator.average_review_time_seconds = time_spent_seconds

                # Update reputation (accept decisions are considered accurate)
                was_accurate = (decision == 'accept')
                was_disputed = False

                from app.services.reputation_service import reputation_service
                try:
                    await reputation_service.update_reputation_after_moderation(
                        db, str(moderator.id), was_accurate, was_disputed
                    )
                except Exception as rep_error:
                    logger.error(f"Failed to update reputation: {rep_error}")

            await db.commit()
            await db.refresh(moderation)

            logger.info(f"Submitted decision for report {report_id}: {decision}")
            return moderation

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to submit decision: {e}")
            return None

    async def get_moderator_stats(
        self,
        db: AsyncSession,
        moderator_id: str,
        period_days: int = 30,
    ) -> Dict:
        """Get moderator statistics"""
        try:
            moderator = await db.execute(
                select(Moderator).where(Moderator.id == moderator_id)
            )
            moderator = moderator.scalar_one_or_none()

            if not moderator:
                return {}

            # Get moderation counts for period
            since = datetime.utcnow() - timedelta(days=period_days)

            moderations = await db.execute(
                select(Moderation).where(
                    and_(
                        Moderation.moderator_id == moderator_id,
                        Moderation.created_at >= since
                    )
                )
            )
            moderations = list(moderations.scalars().all())

            # Count by decision
            decisions = {}
            total_time = 0
            for mod in moderations:
                if mod.decision:
                    decisions[mod.decision] = decisions.get(mod.decision, 0) + 1
                if mod.time_spent_seconds:
                    total_time += mod.time_spent_seconds

            avg_time = total_time / len(moderations) if moderations else 0

            return {
                "moderator_id": str(moderator.id),
                "wallet_address": moderator.wallet_address,
                "reputation_score": moderator.reputation_score,
                "tier": moderator.tier,
                "total_reviews": moderator.total_reviews,
                "accurate_reviews": moderator.accurate_reviews,
                "disputed_reviews": moderator.disputed_reviews,
                "accuracy_rate": moderator.accuracy_rate,
                "period_days": period_days,
                "reviews_in_period": len(moderations),
                "decisions": decisions,
                "average_review_time_seconds": int(avg_time),
                "is_active": moderator.is_active,
                "is_suspended": moderator.is_suspended,
            }

        except Exception as e:
            logger.error(f"Failed to get moderator stats: {e}")
            return {}

    async def get_moderation_history(
        self,
        db: AsyncSession,
        moderator_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Moderation], int]:
        """Get moderation history for a moderator"""
        try:
            # Base query
            query = select(Moderation).where(
                Moderation.moderator_id == moderator_id
            )

            # Count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            # Order by most recent
            query = query.order_by(desc(Moderation.created_at))
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            moderations = list(result.scalars().all())

            return moderations, total

        except Exception as e:
            logger.error(f"Failed to get moderation history: {e}")
            return [], 0

    async def create_or_update_moderator(
        self,
        db: AsyncSession,
        wallet_address: str,
        public_key: Optional[str] = None,
    ) -> Optional[Moderator]:
        """Create or update moderator account"""
        try:
            # Check if exists
            result = await db.execute(
                select(Moderator).where(Moderator.wallet_address == wallet_address)
            )
            moderator = result.scalar_one_or_none()

            if moderator:
                # Update last active
                moderator.last_active_at = datetime.utcnow()
                if public_key:
                    moderator.public_key = public_key
            else:
                # Create new
                moderator = Moderator(
                    wallet_address=wallet_address,
                    public_key=public_key,
                    last_active_at=datetime.utcnow(),
                )
                db.add(moderator)

            await db.commit()
            await db.refresh(moderator)

            logger.info(f"Created/updated moderator {wallet_address}")
            return moderator

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create/update moderator: {e}")
            return None

    async def generate_daily_anchor_data(
        self,
        db: AsyncSession,
        date: datetime,
    ) -> Optional[Dict]:
        """
        Generate daily anchor data (Merkle root of all reports)
        This will be called by Celery task
        """
        try:
            # Get all verified reports for the day
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            reports = await db.execute(
                select(Report).where(
                    and_(
                        Report.status == ReportStatus.VERIFIED,
                        Report.reviewed_at >= start_of_day,
                        Report.reviewed_at < end_of_day
                    )
                )
            )
            reports = list(reports.scalars().all())

            if not reports:
                logger.info(f"No verified reports for {date.date()}")
                return None

            # Generate Merkle tree
            # Use commitment hashes as leaves
            leaves = [r.commitment_hash for r in reports]
            merkle_root = self._compute_merkle_root(leaves)

            return {
                "date": date.date().isoformat(),
                "merkle_root": merkle_root,
                "report_count": len(reports),
                "commitment_hashes": leaves,
            }

        except Exception as e:
            logger.error(f"Failed to generate anchor data: {e}")
            return None

    def _compute_merkle_root(self, leaves: List[str]) -> str:
        """Compute Merkle root from list of hashes"""
        if not leaves:
            return "0x" + "0" * 64

        # Convert to bytes
        current_level = [bytes.fromhex(leaf.replace("0x", "")) for leaf in leaves]

        # Build tree
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Hash pair
                    combined = current_level[i] + current_level[i + 1]
                else:
                    # Odd number, duplicate last
                    combined = current_level[i] + current_level[i]

                hash_result = hashlib.sha256(combined).digest()
                next_level.append(hash_result)

            current_level = next_level

        # Return root as hex
        return "0x" + current_level[0].hex()

    async def analyze_report_with_ai(
        self,
        db: AsyncSession,
        report_id: str,
    ) -> Optional[Dict]:
        """
        Run AI analysis on a report to assist moderation

        Returns:
        - Credibility score
        - Anomaly detection results
        - Triage recommendation
        - AI-suggested actions
        """
        try:
            # Get report
            report = await db.execute(
                select(Report).where(Report.id == report_id)
            )
            report = report.scalar_one_or_none()

            if not report:
                logger.warning(f"Report {report_id} not found")
                return None

            # Prepare text and metadata
            text = f"{report.encrypted_title or ''}\n\n{report.encrypted_summary or ''}"
            metadata = {
                'file_size': report.file_size,
                'file_type': report.file_type,
                'submission_timestamp': report.submission_timestamp,
                'anonymous': report.anonymous,
                'visibility': report.visibility.value if report.visibility else None,
            }

            # Get recent reports for pattern analysis
            recent_stmt = select(Report).order_by(desc(Report.created_at)).limit(50)
            recent_result = await db.execute(recent_stmt)
            recent_reports = recent_result.scalars().all()

            recent_reports_data = [
                {
                    'id': str(r.id),
                    'text': f"{r.encrypted_title or ''} {r.encrypted_summary or ''}",
                    'submission_timestamp': r.submission_timestamp
                }
                for r in recent_reports
            ]

            # Run AI analysis
            credibility = credibility_scorer.score_report(text, metadata)
            anomalies = anomaly_detector.detect_anomalies(text, metadata, recent_reports_data)
            triage = report_triager.triage_report(text, metadata, recent_reports_data)

            # Update report with AI assessment
            report.verification_score = credibility['credibility_score']
            report.risk_level = credibility['risk_level']

            await db.commit()

            return {
                'report_id': str(report_id),
                'credibility': credibility,
                'anomalies': anomalies,
                'triage': triage,
                'recommendation': triage['recommendation'],
                'priority': triage['priority'],
            }

        except Exception as e:
            logger.error(f"AI analysis failed for report {report_id}: {e}")
            return None

    async def batch_analyze_queue(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> Dict:
        """
        Run AI analysis on pending reports to optimize queue

        Returns:
        - Total analyzed
        - Priority distribution
        - High-priority reports
        """
        try:
            # Get pending reports
            stmt = select(Report).where(
                and_(
                    Report.status == ReportStatus.PENDING,
                    Report.deleted_at.is_(None)
                )
            ).limit(limit)

            result = await db.execute(stmt)
            reports = result.scalars().all()

            priority_counts = {'urgent': 0, 'high': 0, 'medium': 0, 'low': 0}
            high_priority_reports = []
            total_analyzed = 0

            for report in reports:
                text = f"{report.encrypted_title or ''}\n\n{report.encrypted_summary or ''}"
                metadata = {
                    'file_size': report.file_size,
                    'submission_timestamp': report.submission_timestamp,
                }

                # Run triage
                triage = report_triager.triage_report(text, metadata)

                # Update report
                if triage['ai_analysis'].get('credibility'):
                    report.verification_score = triage['ai_analysis']['credibility']['credibility_score']
                    report.risk_level = triage['ai_analysis']['credibility']['risk_level']

                priority = triage['priority']
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

                if priority in ['urgent', 'high']:
                    high_priority_reports.append({
                        'report_id': str(report.id),
                        'priority': priority,
                        'credibility_score': report.verification_score,
                        'risk_level': report.risk_level,
                    })

                total_analyzed += 1

            await db.commit()

            return {
                'total_analyzed': total_analyzed,
                'priority_distribution': priority_counts,
                'high_priority_count': len(high_priority_reports),
                'high_priority_reports': high_priority_reports[:10],  # Top 10
            }

        except Exception as e:
            logger.error(f"Batch queue analysis failed: {e}")
            return {'error': str(e)}


# Singleton instance
moderation_service = ModerationService()
