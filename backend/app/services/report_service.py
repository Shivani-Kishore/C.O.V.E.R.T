"""
C.O.V.E.R.T - Report Service
Business logic for report management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Tuple
from datetime import datetime
from uuid import UUID
import logging

from app.models.report import Report, ReportStatus, ReportVisibility, ReportLog

logger = logging.getLogger(__name__)


class ReportService:
    """Service for managing reports"""

    async def create_report(
        self,
        db: AsyncSession,
        cid: str,
        cid_hash: str,
        tx_hash: str,
        category: str,
        visibility: int,
        size_bytes: int,
        reporter_id: str,
    ) -> Report:
        """Create a new report"""
        try:
            # Map visibility int to enum
            visibility_map = {
                0: ReportVisibility.PRIVATE,
                1: ReportVisibility.MODERATED,
                2: ReportVisibility.PUBLIC,
            }
            vis_enum = visibility_map.get(visibility, ReportVisibility.MODERATED)

            report = Report(
                cid=cid,
                cid_hash=cid_hash,
                tx_hash=tx_hash,
                category=category,
                visibility=visibility,
                size_bytes=size_bytes,
                reporter_id=reporter_id,
                status=ReportStatus.PENDING,
                submitted_at=datetime.utcnow(),
            )

            db.add(report)

            # Create log entry
            log = ReportLog(
                report_id=report.id,
                event_type="created",
                event_data={"category": category, "visibility": visibility},
            )
            db.add(log)

            await db.commit()
            await db.refresh(report)

            logger.info(f"Created report {report.id} with CID {cid[:20]}...")
            return report

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create report: {e}")
            raise

    async def get_report_by_id(
        self,
        db: AsyncSession,
        report_id: str,
    ) -> Optional[Report]:
        """Get a report by ID"""
        try:
            result = await db.execute(
                select(Report).where(
                    and_(
                        Report.id == report_id,
                        Report.deleted_at.is_(None)
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}")
            return None

    async def get_user_reports(
        self,
        db: AsyncSession,
        reporter_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Report], int]:
        """Get reports for a specific user with filtering"""
        try:
            # Build query
            query = select(Report).where(
                and_(
                    Report.reporter_id == reporter_id,
                    Report.deleted_at.is_(None)
                )
            )

            # Apply filters
            if status:
                status_enum = ReportStatus(status)
                query = query.where(Report.status == status_enum)

            if category:
                query = query.where(Report.category == category)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            # Apply pagination and ordering
            query = query.order_by(Report.submitted_at.desc())
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            reports = list(result.scalars().all())

            return reports, total

        except Exception as e:
            logger.error(f"Failed to get user reports: {e}")
            return [], 0

    async def delete_report(
        self,
        db: AsyncSession,
        report_id: str,
    ) -> bool:
        """Soft delete a report"""
        try:
            report = await self.get_report_by_id(db, report_id)
            if not report:
                return False

            report.deleted_at = datetime.utcnow()

            # Create log entry
            log = ReportLog(
                report_id=report.id,
                event_type="deleted",
            )
            db.add(log)

            await db.commit()

            logger.info(f"Deleted report {report_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete report {report_id}: {e}")
            return False

    async def update_blockchain_info(
        self,
        db: AsyncSession,
        report_id: str,
        tx_hash: str,
        block_number: Optional[int] = None,
    ) -> Optional[Report]:
        """Update report with blockchain transaction info"""
        try:
            report = await self.get_report_by_id(db, report_id)
            if not report:
                return None

            report.tx_hash = tx_hash
            if block_number:
                report.block_number = block_number

            # Create log entry
            log = ReportLog(
                report_id=report.id,
                event_type="blockchain_committed",
                event_data={"tx_hash": tx_hash, "block_number": block_number},
            )
            db.add(log)

            await db.commit()
            await db.refresh(report)

            logger.info(f"Updated blockchain info for report {report_id}")
            return report

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update blockchain info: {e}")
            return None

    async def update_status(
        self,
        db: AsyncSession,
        report_id: str,
        status: ReportStatus,
        actor_id: Optional[str] = None,
    ) -> Optional[Report]:
        """Update report status"""
        try:
            report = await self.get_report_by_id(db, report_id)
            if not report:
                return None

            old_status = report.status
            report.status = status

            if status in [ReportStatus.VERIFIED, ReportStatus.REJECTED]:
                report.reviewed_at = datetime.utcnow()

            # Create log entry
            log = ReportLog(
                report_id=report.id,
                event_type="status_changed",
                event_data={"old_status": old_status.value, "new_status": status.value},
                actor_id=actor_id,
            )
            db.add(log)

            await db.commit()
            await db.refresh(report)

            logger.info(f"Updated report {report_id} status to {status.value}")
            return report

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update status: {e}")
            return None

    async def update_verification_score(
        self,
        db: AsyncSession,
        report_id: str,
        score: float,
        risk_level: str,
    ) -> Optional[Report]:
        """Update AI verification score and risk level"""
        try:
            report = await self.get_report_by_id(db, report_id)
            if not report:
                return None

            report.verification_score = score
            report.risk_level = risk_level

            await db.commit()
            await db.refresh(report)

            logger.info(f"Updated verification score for report {report_id}: {score}")
            return report

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update verification score: {e}")
            return None

    async def get_reports_for_moderation(
        self,
        db: AsyncSession,
        status: ReportStatus = ReportStatus.PENDING,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Report], int]:
        """Get reports pending moderation"""
        try:
            query = select(Report).where(
                and_(
                    Report.status == status,
                    Report.visibility != 0,  # Not private
                    Report.deleted_at.is_(None)
                )
            )

            if category:
                query = query.where(Report.category == category)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            # Order by oldest first
            query = query.order_by(Report.submitted_at.asc())
            query = query.limit(limit).offset(offset)

            result = await db.execute(query)
            reports = list(result.scalars().all())

            return reports, total

        except Exception as e:
            logger.error(f"Failed to get moderation queue: {e}")
            return [], 0

    async def get_report_stats(
        self,
        db: AsyncSession,
        reporter_id: Optional[str] = None,
    ) -> dict:
        """Get report statistics"""
        try:
            base_query = select(Report).where(Report.deleted_at.is_(None))

            if reporter_id:
                base_query = base_query.where(Report.reporter_id == reporter_id)

            # Total
            total_result = await db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total = total_result.scalar() or 0

            # By status
            stats = {"total": total}
            for status in ReportStatus:
                status_query = base_query.where(Report.status == status)
                result = await db.execute(
                    select(func.count()).select_from(status_query.subquery())
                )
                stats[status.value] = result.scalar() or 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get report stats: {e}")
            return {"total": 0}


# Singleton instance
report_service = ReportService()
