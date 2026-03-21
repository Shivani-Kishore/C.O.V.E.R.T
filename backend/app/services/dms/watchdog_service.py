"""
C.O.V.E.R.T - DMS Watchdog Service

Background service that monitors DMS triggers and executes releases
"""

import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from datetime import datetime, timedelta
import time

from app.models.dms import DeadMansSwitch, DMSWatchdog, DMSStatus
from app.services.dms.dms_service import dms_service
from app.services.dms.release_service import release_service

logger = logging.getLogger(__name__)


class WatchdogService:
    """
    Background watchdog service for DMS monitoring

    Runs continuously to:
    1. Check for DMS that have reached trigger date
    2. Trigger and release reports
    3. Retry failed releases
    4. Track service health
    """

    def __init__(self):
        self.check_interval_seconds = 300  # 5 minutes
        self.batch_size = 100
        self.is_running = False
        self.watchdog_id = None

    async def start(self, db: AsyncSession):
        """
        Start the watchdog service

        Args:
            db: Database session
        """
        if self.is_running:
            logger.warning("Watchdog already running")
            return

        self.is_running = True

        # Create watchdog record
        watchdog = DMSWatchdog(
            service_name="dms_watchdog",
            is_active=True,
            last_heartbeat=datetime.utcnow(),
            check_interval_seconds=self.check_interval_seconds,
            batch_size=self.batch_size,
            started_at=datetime.utcnow()
        )
        db.add(watchdog)
        await db.commit()
        await db.refresh(watchdog)

        self.watchdog_id = watchdog.id

        logger.info(f"Watchdog service started (ID: {self.watchdog_id})")

        try:
            while self.is_running:
                await self._run_check_cycle(db)
                await asyncio.sleep(self.check_interval_seconds)
        except Exception as e:
            logger.error(f"Watchdog service error: {e}")
            self.is_running = False
        finally:
            await self._stop(db)

    async def stop(self, db: AsyncSession):
        """Stop the watchdog service"""
        self.is_running = False
        await self._stop(db)

    async def _stop(self, db: AsyncSession):
        """Internal stop method"""
        if self.watchdog_id:
            watchdog = await db.execute(
                select(DMSWatchdog).where(DMSWatchdog.id == self.watchdog_id)
            )
            watchdog = watchdog.scalar_one_or_none()

            if watchdog:
                watchdog.is_active = False
                watchdog.stopped_at = datetime.utcnow()
                await db.commit()

            logger.info(f"Watchdog service stopped (ID: {self.watchdog_id})")

    async def _run_check_cycle(self, db: AsyncSession):
        """
        Run a single check cycle

        Steps:
        1. Update heartbeat
        2. Get pending triggers
        3. Process each trigger
        4. Update statistics
        """
        start_time = time.time()

        try:
            # Update heartbeat
            await self._update_heartbeat(db)

            # Get pending triggers
            pending_dms = await dms_service.get_pending_triggers(db, limit=self.batch_size)

            if not pending_dms:
                logger.debug("No pending DMS triggers found")
                await self._update_statistics(db, 0, 0, 0, 0, start_time)
                return

            logger.info(f"Found {len(pending_dms)} pending DMS triggers")

            # Process each DMS
            triggers_processed = 0
            releases_attempted = 0
            releases_succeeded = 0
            releases_failed = 0

            for dms in pending_dms:
                try:
                    # Trigger DMS
                    triggered = await release_service.trigger_dms(db, str(dms.id))

                    if triggered:
                        triggers_processed += 1

                        # Release report
                        logger.info(f"Releasing report for DMS {dms.id}")
                        releases_attempted += 1

                        result = await release_service.release_report(db, str(dms.id))

                        if result.get('success'):
                            releases_succeeded += 1
                            logger.info(f"DMS {dms.id} released successfully")
                        else:
                            releases_failed += 1
                            logger.warning(f"DMS {dms.id} release failed: {result.get('error')}")

                except Exception as e:
                    releases_failed += 1
                    logger.error(f"Failed to process DMS {dms.id}: {e}")

            # Update statistics
            await self._update_statistics(
                db,
                triggers_processed,
                releases_attempted,
                releases_succeeded,
                releases_failed,
                start_time
            )

            logger.info(
                f"Check cycle complete: {triggers_processed} triggered, "
                f"{releases_succeeded}/{releases_attempted} released"
            )

        except Exception as e:
            logger.error(f"Check cycle error: {e}")
            await self._record_error(db, str(e))

    async def _update_heartbeat(self, db: AsyncSession):
        """Update watchdog heartbeat"""
        if not self.watchdog_id:
            return

        try:
            await db.execute(
                update(DMSWatchdog)
                .where(DMSWatchdog.id == self.watchdog_id)
                .values(last_heartbeat=datetime.utcnow())
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")

    async def _update_statistics(
        self,
        db: AsyncSession,
        triggers_found: int,
        releases_attempted: int,
        releases_succeeded: int,
        releases_failed: int,
        start_time: float
    ):
        """Update watchdog statistics"""
        if not self.watchdog_id:
            return

        try:
            duration_ms = int((time.time() - start_time) * 1000)

            watchdog = await db.execute(
                select(DMSWatchdog).where(DMSWatchdog.id == self.watchdog_id)
            )
            watchdog = watchdog.scalar_one_or_none()

            if watchdog:
                watchdog.total_checks += 1
                watchdog.triggers_found += triggers_found
                watchdog.releases_attempted += releases_attempted
                watchdog.releases_succeeded += releases_succeeded
                watchdog.releases_failed += releases_failed
                watchdog.last_check_duration_ms = duration_ms

                # Update average duration
                if watchdog.avg_check_duration_ms:
                    watchdog.avg_check_duration_ms = int(
                        (watchdog.avg_check_duration_ms * (watchdog.total_checks - 1) + duration_ms) /
                        watchdog.total_checks
                    )
                else:
                    watchdog.avg_check_duration_ms = duration_ms

                # Reset consecutive errors on success
                if releases_failed == 0:
                    watchdog.consecutive_errors = 0

                await db.commit()

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    async def _record_error(self, db: AsyncSession, error_message: str):
        """Record watchdog error"""
        if not self.watchdog_id:
            return

        try:
            watchdog = await db.execute(
                select(DMSWatchdog).where(DMSWatchdog.id == self.watchdog_id)
            )
            watchdog = watchdog.scalar_one_or_none()

            if watchdog:
                watchdog.last_error = error_message
                watchdog.last_error_at = datetime.utcnow()
                watchdog.consecutive_errors += 1

                await db.commit()

        except Exception as e:
            logger.error(f"Failed to record error: {e}")

    async def get_status(self, db: AsyncSession) -> dict:
        """Get watchdog service status"""
        if not self.watchdog_id:
            return {'status': 'not_running'}

        try:
            watchdog = await db.execute(
                select(DMSWatchdog).where(DMSWatchdog.id == self.watchdog_id)
            )
            watchdog = watchdog.scalar_one_or_none()

            if not watchdog:
                return {'status': 'not_found'}

            # Check if heartbeat is stale
            stale_threshold = datetime.utcnow() - timedelta(
                seconds=self.check_interval_seconds * 2
            )
            is_healthy = watchdog.last_heartbeat > stale_threshold

            return {
                'status': 'running' if watchdog.is_active and is_healthy else 'stale',
                'service_name': watchdog.service_name,
                'is_active': watchdog.is_active,
                'last_heartbeat': watchdog.last_heartbeat,
                'total_checks': watchdog.total_checks,
                'triggers_found': watchdog.triggers_found,
                'releases_attempted': watchdog.releases_attempted,
                'releases_succeeded': watchdog.releases_succeeded,
                'releases_failed': watchdog.releases_failed,
                'avg_check_duration_ms': watchdog.avg_check_duration_ms,
                'last_check_duration_ms': watchdog.last_check_duration_ms,
                'check_interval_seconds': watchdog.check_interval_seconds,
                'consecutive_errors': watchdog.consecutive_errors,
                'last_error': watchdog.last_error,
                'last_error_at': watchdog.last_error_at,
            }

        except Exception as e:
            logger.error(f"Failed to get watchdog status: {e}")
            return {'status': 'error', 'error': str(e)}

    async def manual_trigger_check(self, db: AsyncSession) -> dict:
        """Manually trigger a check cycle (for testing/admin use)"""
        logger.info("Manual check trigger requested")
        start_time = time.time()

        try:
            pending_dms = await dms_service.get_pending_triggers(db, limit=self.batch_size)

            results = {
                'pending_count': len(pending_dms),
                'processed': []
            }

            for dms in pending_dms:
                try:
                    triggered = await release_service.trigger_dms(db, str(dms.id))

                    if triggered:
                        result = await release_service.release_report(db, str(dms.id))
                        results['processed'].append({
                            'dms_id': str(dms.id),
                            'report_id': str(dms.report_id),
                            'success': result.get('success', False),
                            'error': result.get('error')
                        })

                except Exception as e:
                    results['processed'].append({
                        'dms_id': str(dms.id),
                        'success': False,
                        'error': str(e)
                    })

            duration_ms = int((time.time() - start_time) * 1000)
            results['duration_ms'] = duration_ms

            return results

        except Exception as e:
            logger.error(f"Manual trigger check failed: {e}")
            return {'success': False, 'error': str(e)}


# Global instance
watchdog_service = WatchdogService()
