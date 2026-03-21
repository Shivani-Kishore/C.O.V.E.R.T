"""
C.O.V.E.R.T - Dead Man's Switch Service

Core DMS functionality for automated report release
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta

from app.models.dms import (
    DeadMansSwitch,
    DMSCheckIn,
    DMSReleaseLog,
    DMSStatus,
    DMSTriggerType
)
from app.models.report import Report, ReportStatus, ReportVisibility

logger = logging.getLogger(__name__)


class DMSService:
    """Service for managing Dead Man's Switch functionality"""

    async def create_dms(
        self,
        db: AsyncSession,
        report_id: str,
        reporter_nullifier: str,
        trigger_date: datetime,
        trigger_type: str = "time_based",
        **kwargs
    ) -> Optional[DeadMansSwitch]:
        """
        Create a new Dead Man's Switch for a report

        Args:
            db: Database session
            report_id: Report UUID
            reporter_nullifier: Reporter's nullifier for verification
            trigger_date: When to trigger DMS
            trigger_type: Type of trigger (time_based, activity_based, manual)
            **kwargs: Additional DMS configuration

        Returns:
            Created DeadMansSwitch or None on error
        """
        try:
            # Verify report exists and belongs to reporter
            report = await db.execute(
                select(Report).where(
                    and_(
                        Report.id == report_id,
                        Report.reporter_nullifier == reporter_nullifier
                    )
                )
            )
            report = report.scalar_one_or_none()

            if not report:
                logger.warning(f"Report {report_id} not found or nullifier mismatch")
                return None

            # Check if DMS already exists for this report
            existing = await db.execute(
                select(DeadMansSwitch).where(DeadMansSwitch.report_id == report_id)
            )
            if existing.scalar_one_or_none():
                logger.warning(f"DMS already exists for report {report_id}")
                return None

            # Create DMS
            dms = DeadMansSwitch(
                report_id=report_id,
                reporter_nullifier=reporter_nullifier,
                reporter_commitment=kwargs.get('reporter_commitment'),
                trigger_type=DMSTriggerType(trigger_type),
                trigger_date=trigger_date,
                inactivity_days=kwargs.get('inactivity_days'),
                status=DMSStatus.ACTIVE,
                auto_release_public=kwargs.get('auto_release_public', True),
                auto_pin_ipfs=kwargs.get('auto_pin_ipfs', True),
                notify_contacts=kwargs.get('notify_contacts', False),
                encrypted_contacts=kwargs.get('encrypted_contacts'),
            )

            db.add(dms)

            # Update report DMS flags
            report.dms_enabled = True
            report.dms_trigger_date = trigger_date
            report.dms_released = False

            await db.commit()
            await db.refresh(dms)

            logger.info(f"Created DMS {dms.id} for report {report_id}")
            return dms

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create DMS: {e}")
            return None

    async def check_in(
        self,
        db: AsyncSession,
        dms_id: str,
        reporter_nullifier: str,
        **kwargs
    ) -> Optional[DMSCheckIn]:
        """
        Reporter check-in to reset/extend DMS trigger

        Args:
            db: Database session
            dms_id: DMS UUID
            reporter_nullifier: Reporter's nullifier for verification
            **kwargs: Additional check-in data

        Returns:
            Created DMSCheckIn or None on error
        """
        try:
            # Get DMS and verify reporter
            dms = await db.execute(
                select(DeadMansSwitch).where(
                    and_(
                        DeadMansSwitch.id == dms_id,
                        DeadMansSwitch.reporter_nullifier == reporter_nullifier,
                        DeadMansSwitch.status == DMSStatus.ACTIVE
                    )
                )
            )
            dms = dms.scalar_one_or_none()

            if not dms:
                logger.warning(f"DMS {dms_id} not found or unauthorized")
                return None

            # Create check-in record
            check_in = DMSCheckIn(
                dms_id=dms_id,
                check_in_timestamp=datetime.utcnow(),
                proof_of_life=kwargs.get('proof_of_life'),
                zkp_nullifier=reporter_nullifier,
                zkp_proof=kwargs.get('zkp_proof'),
                extended_trigger_date=kwargs.get('extend_trigger_date'),
                extension_reason=kwargs.get('extension_reason'),
            )

            db.add(check_in)

            # Update DMS
            dms.last_check_in = check_in.check_in_timestamp
            dms.check_in_count += 1

            # Extend trigger date if requested
            if kwargs.get('extend_trigger_date'):
                old_date = dms.trigger_date
                dms.trigger_date = kwargs.get('extend_trigger_date')
                dms.status = DMSStatus.EXTENDED

                # Update report trigger date
                report = await db.execute(
                    select(Report).where(Report.id == dms.report_id)
                )
                report = report.scalar_one_or_none()
                if report:
                    report.dms_trigger_date = dms.trigger_date

                logger.info(f"Extended DMS {dms_id} from {old_date} to {dms.trigger_date}")

            await db.commit()
            await db.refresh(check_in)

            logger.info(f"Check-in recorded for DMS {dms_id}, count: {dms.check_in_count}")
            return check_in

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to record check-in: {e}")
            return None

    async def cancel_dms(
        self,
        db: AsyncSession,
        dms_id: str,
        reporter_nullifier: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Cancel a Dead Man's Switch

        Args:
            db: Database session
            dms_id: DMS UUID
            reporter_nullifier: Reporter's nullifier for verification
            reason: Cancellation reason

        Returns:
            True if cancelled successfully
        """
        try:
            # Get DMS and verify reporter
            dms = await db.execute(
                select(DeadMansSwitch).where(
                    and_(
                        DeadMansSwitch.id == dms_id,
                        DeadMansSwitch.reporter_nullifier == reporter_nullifier
                    )
                )
            )
            dms = dms.scalar_one_or_none()

            if not dms:
                logger.warning(f"DMS {dms_id} not found or unauthorized")
                return False

            if dms.status == DMSStatus.RELEASED:
                logger.warning(f"Cannot cancel DMS {dms_id} - already released")
                return False

            # Update DMS status
            dms.status = DMSStatus.CANCELLED
            dms.cancelled_at = datetime.utcnow()

            # Update report
            report = await db.execute(
                select(Report).where(Report.id == dms.report_id)
            )
            report = report.scalar_one_or_none()
            if report:
                report.dms_enabled = False

            await db.commit()

            logger.info(f"Cancelled DMS {dms_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to cancel DMS: {e}")
            return False

    async def get_dms_by_report(
        self,
        db: AsyncSession,
        report_id: str
    ) -> Optional[DeadMansSwitch]:
        """Get DMS for a specific report"""
        try:
            result = await db.execute(
                select(DeadMansSwitch).where(DeadMansSwitch.report_id == report_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get DMS for report {report_id}: {e}")
            return None

    async def get_dms_by_nullifier(
        self,
        db: AsyncSession,
        reporter_nullifier: str
    ) -> List[DeadMansSwitch]:
        """Get all DMS for a reporter"""
        try:
            result = await db.execute(
                select(DeadMansSwitch).where(
                    DeadMansSwitch.reporter_nullifier == reporter_nullifier
                ).order_by(DeadMansSwitch.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get DMS for nullifier: {e}")
            return []

    async def get_pending_triggers(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> List[DeadMansSwitch]:
        """
        Get DMS that have reached trigger date and need processing

        Returns:
            List of DMS ready for triggering
        """
        try:
            now = datetime.utcnow()

            result = await db.execute(
                select(DeadMansSwitch).where(
                    and_(
                        DeadMansSwitch.status == DMSStatus.ACTIVE,
                        DeadMansSwitch.trigger_date <= now,
                        DeadMansSwitch.cancelled_at.is_(None)
                    )
                ).order_by(DeadMansSwitch.trigger_date.asc()).limit(limit)
            )

            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get pending triggers: {e}")
            return []

    async def get_dms_statistics(
        self,
        db: AsyncSession
    ) -> Dict:
        """Get DMS system statistics"""
        try:
            now = datetime.utcnow()
            day_ago = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)

            # Status counts
            total_active = await db.execute(
                select(func.count()).where(DeadMansSwitch.status == DMSStatus.ACTIVE)
            )
            total_triggered = await db.execute(
                select(func.count()).where(DeadMansSwitch.status == DMSStatus.TRIGGERED)
            )
            total_released = await db.execute(
                select(func.count()).where(DeadMansSwitch.status == DMSStatus.RELEASED)
            )
            total_cancelled = await db.execute(
                select(func.count()).where(DeadMansSwitch.status == DMSStatus.CANCELLED)
            )

            # Pending triggers
            triggers_24h = await db.execute(
                select(func.count()).where(
                    and_(
                        DeadMansSwitch.status == DMSStatus.ACTIVE,
                        DeadMansSwitch.trigger_date <= now + timedelta(days=1)
                    )
                )
            )
            triggers_7d = await db.execute(
                select(func.count()).where(
                    and_(
                        DeadMansSwitch.status == DMSStatus.ACTIVE,
                        DeadMansSwitch.trigger_date <= now + timedelta(days=7)
                    )
                )
            )

            # Check-in stats
            check_ins_today = await db.execute(
                select(func.count()).where(
                    DMSCheckIn.check_in_timestamp >= day_ago
                )
            )

            # Release stats
            releases_today = await db.execute(
                select(func.count()).where(
                    and_(
                        DeadMansSwitch.released_at >= day_ago,
                        DeadMansSwitch.status == DMSStatus.RELEASED
                    )
                )
            )

            return {
                'total_active': total_active.scalar() or 0,
                'total_triggered': total_triggered.scalar() or 0,
                'total_released': total_released.scalar() or 0,
                'total_cancelled': total_cancelled.scalar() or 0,
                'pending_triggers_24h': triggers_24h.scalar() or 0,
                'pending_triggers_7d': triggers_7d.scalar() or 0,
                'total_check_ins_today': check_ins_today.scalar() or 0,
                'total_releases_today': releases_today.scalar() or 0,
            }

        except Exception as e:
            logger.error(f"Failed to get DMS statistics: {e}")
            return {}


# Global instance
dms_service = DMSService()
