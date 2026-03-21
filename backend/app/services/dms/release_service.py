"""
C.O.V.E.R.T - DMS Release Service

Handles automated report release when DMS triggers
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, List
from datetime import datetime

from app.models.dms import (
    DeadMansSwitch,
    DMSReleaseLog,
    DMSStatus
)
from app.models.report import Report, ReportStatus, ReportVisibility

logger = logging.getLogger(__name__)


class ReleaseService:
    """Service for handling DMS report releases"""

    def __init__(self):
        self.max_retry_attempts = 3
        self.retry_delay_minutes = 30

    async def trigger_dms(
        self,
        db: AsyncSession,
        dms_id: str
    ) -> bool:
        """
        Mark DMS as triggered (trigger date reached)

        Args:
            db: Database session
            dms_id: DMS UUID

        Returns:
            True if triggered successfully
        """
        try:
            dms = await db.execute(
                select(DeadMansSwitch).where(DeadMansSwitch.id == dms_id)
            )
            dms = dms.scalar_one_or_none()

            if not dms:
                logger.warning(f"DMS {dms_id} not found")
                return False

            if dms.status != DMSStatus.ACTIVE:
                logger.warning(f"DMS {dms_id} not active, status: {dms.status}")
                return False

            # Mark as triggered
            dms.status = DMSStatus.TRIGGERED
            dms.trigger_reached_at = datetime.utcnow()

            # Log trigger event
            log = DMSReleaseLog(
                dms_id=dms_id,
                attempt_number=1,
                action_type='trigger',
                action_success=True,
                action_details={'triggered_at': datetime.utcnow().isoformat()}
            )
            db.add(log)

            await db.commit()

            logger.info(f"DMS {dms_id} triggered")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to trigger DMS {dms_id}: {e}")
            return False

    async def release_report(
        self,
        db: AsyncSession,
        dms_id: str
    ) -> Dict:
        """
        Execute automated report release

        Steps:
        1. Update report visibility to public
        2. Pin to IPFS (if enabled)
        3. Post blockchain transaction (optional)
        4. Send notifications (if enabled)

        Args:
            db: Database session
            dms_id: DMS UUID

        Returns:
            Dictionary with release results
        """
        try:
            # Get DMS
            dms = await db.execute(
                select(DeadMansSwitch).where(DeadMansSwitch.id == dms_id)
            )
            dms = dms.scalar_one_or_none()

            if not dms:
                return {'success': False, 'error': 'DMS not found'}

            if dms.status == DMSStatus.RELEASED:
                return {'success': False, 'error': 'Already released'}

            # Get report
            report = await db.execute(
                select(Report).where(Report.id == dms.report_id)
            )
            report = report.scalar_one_or_none()

            if not report:
                return {'success': False, 'error': 'Report not found'}

            # Increment attempt counter
            dms.release_attempts += 1
            dms.last_release_attempt = datetime.utcnow()

            attempt_number = dms.release_attempts
            results = {'success': True, 'steps': []}

            # Step 1: Update report visibility
            try:
                if dms.auto_release_public:
                    report.visibility = ReportVisibility.PUBLIC
                    report.status = ReportStatus.VERIFIED
                    results['steps'].append({
                        'action': 'visibility_update',
                        'success': True,
                        'visibility': 'public'
                    })
                    logger.info(f"Report {report.id} visibility updated to PUBLIC")
            except Exception as e:
                results['steps'].append({
                    'action': 'visibility_update',
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"Failed to update visibility: {e}")

            # Step 2: Pin to IPFS
            ipfs_cid = None
            if dms.auto_pin_ipfs:
                try:
                    ipfs_result = await self._pin_to_ipfs(report)
                    ipfs_cid = ipfs_result.get('cid')
                    results['steps'].append({
                        'action': 'ipfs_pin',
                        'success': ipfs_result.get('success', False),
                        'cid': ipfs_cid
                    })
                except Exception as e:
                    results['steps'].append({
                        'action': 'ipfs_pin',
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Failed to pin to IPFS: {e}")

            # Step 3: Blockchain transaction (optional)
            transaction_hash = None
            try:
                tx_result = await self._post_blockchain_release(report, dms)
                transaction_hash = tx_result.get('transaction_hash')
                results['steps'].append({
                    'action': 'blockchain_tx',
                    'success': tx_result.get('success', False),
                    'tx_hash': transaction_hash
                })
            except Exception as e:
                results['steps'].append({
                    'action': 'blockchain_tx',
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"Failed blockchain transaction: {e}")

            # Step 4: Send notifications
            notifications_sent = 0
            if dms.notify_contacts and dms.encrypted_contacts:
                try:
                    notify_result = await self._send_notifications(dms, report)
                    notifications_sent = notify_result.get('sent_count', 0)
                    results['steps'].append({
                        'action': 'notifications',
                        'success': notify_result.get('success', False),
                        'sent_count': notifications_sent
                    })
                except Exception as e:
                    results['steps'].append({
                        'action': 'notifications',
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Failed to send notifications: {e}")

            # Update DMS status
            all_success = all(step.get('success', False) for step in results['steps'])

            if all_success or dms.release_attempts >= self.max_retry_attempts:
                dms.status = DMSStatus.RELEASED
                dms.released_at = datetime.utcnow()
                dms.release_transaction_hash = transaction_hash
                dms.release_ipfs_cid = ipfs_cid

                # Update report
                report.dms_released = True

                logger.info(f"DMS {dms_id} released successfully")
            else:
                dms.status = DMSStatus.FAILED
                dms.failure_reason = f"Release failed after {dms.release_attempts} attempts"
                logger.warning(f"DMS {dms_id} release failed")

            # Log release attempt
            log = DMSReleaseLog(
                dms_id=dms_id,
                attempt_number=attempt_number,
                action_type='release',
                action_success=all_success,
                action_details=results,
                transaction_hash=transaction_hash,
                ipfs_cid=ipfs_cid,
                notifications_sent=notifications_sent
            )
            db.add(log)

            await db.commit()

            return results

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to release report for DMS {dms_id}: {e}")

            # Log failure
            try:
                log = DMSReleaseLog(
                    dms_id=dms_id,
                    attempt_number=dms.release_attempts,
                    action_type='release',
                    action_success=False,
                    error_message=str(e)
                )
                db.add(log)
                await db.commit()
            except Exception as log_err:
                logger.warning(f"Failed to log DMS release failure: {log_err}")

            return {'success': False, 'error': str(e)}

    async def _pin_to_ipfs(self, report: Report) -> Dict:
        """
        Pin report to IPFS

        In production, this would:
        1. Get report content from IPFS
        2. Pin to additional IPFS gateways
        3. Pin to Pinata/Infura/other services

        Returns:
            Dict with pin status
        """
        try:
            # Placeholder implementation
            # In production, integrate with IPFS client
            logger.info(f"Pinning report {report.id} to IPFS")

            # Would call IPFS pinning service
            # ipfs_client.pin.add(report.ipfs_cid)
            # pinata.pinByHash(report.ipfs_cid)

            return {
                'success': True,
                'cid': report.ipfs_cid,
                'gateway_url': report.ipfs_gateway_url,
                'pin_status': 'pinned'
            }

        except Exception as e:
            logger.error(f"IPFS pinning failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _post_blockchain_release(self, report: Report, dms: DeadMansSwitch) -> Dict:
        """
        Post release notification to blockchain

        In production, this would call smart contract to:
        1. Record release event
        2. Update commitment status
        3. Emit release event

        Returns:
            Dict with transaction status
        """
        try:
            # Placeholder implementation
            # In production, integrate with Web3
            logger.info(f"Posting DMS release to blockchain for report {report.id}")

            # Would call smart contract
            # tx = contract.functions.recordDMSRelease(
            #     commitment_hash=report.commitment_hash,
            #     ipfs_cid=report.ipfs_cid
            # ).transact()

            return {
                'success': True,
                'transaction_hash': '0x' + '0' * 64,  # Placeholder
                'block_number': 12345678
            }

        except Exception as e:
            logger.error(f"Blockchain transaction failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _send_notifications(self, dms: DeadMansSwitch, report: Report) -> Dict:
        """
        Send notifications to encrypted contact list

        In production, this would:
        1. Decrypt contact list
        2. Send emails/messages
        3. Track delivery status

        Returns:
            Dict with notification status
        """
        try:
            # Placeholder implementation
            logger.info(f"Sending notifications for DMS {dms.id}")

            # Would decrypt contacts and send notifications
            # contacts = decrypt_contacts(dms.encrypted_contacts)
            # for contact in contacts:
            #     send_email(contact, report_info)

            return {
                'success': True,
                'sent_count': len(dms.encrypted_contacts or [])
            }

        except Exception as e:
            logger.error(f"Notification sending failed: {e}")
            return {'success': False, 'error': str(e)}

    async def emergency_override(
        self,
        db: AsyncSession,
        dms_id: str,
        admin_wallet: str,
        action: str,
        reason: str,
        **kwargs
    ) -> bool:
        """
        Admin emergency override of DMS

        Actions:
        - release: Force immediate release
        - cancel: Force cancellation
        - extend: Extend trigger date

        Args:
            db: Database session
            dms_id: DMS UUID
            admin_wallet: Admin wallet address
            action: Override action
            reason: Override reason
            **kwargs: Additional action parameters

        Returns:
            True if override successful
        """
        try:
            dms = await db.execute(
                select(DeadMansSwitch).where(DeadMansSwitch.id == dms_id)
            )
            dms = dms.scalar_one_or_none()

            if not dms:
                logger.warning(f"DMS {dms_id} not found")
                return False

            # Record override
            dms.emergency_override = True
            dms.override_reason = reason
            dms.override_by = admin_wallet
            dms.override_at = datetime.utcnow()

            # Execute action
            if action == 'release':
                result = await self.release_report(db, dms_id)
                success = result.get('success', False)
            elif action == 'cancel':
                dms.status = DMSStatus.CANCELLED
                dms.cancelled_at = datetime.utcnow()
                success = True
            elif action == 'extend':
                if 'extend_until' in kwargs:
                    dms.trigger_date = kwargs['extend_until']
                    dms.status = DMSStatus.EXTENDED
                    success = True
                else:
                    success = False
            else:
                logger.warning(f"Unknown override action: {action}")
                success = False

            if success:
                await db.commit()
                logger.info(f"Emergency override applied to DMS {dms_id}: {action}")

            return success

        except Exception as e:
            await db.rollback()
            logger.error(f"Emergency override failed: {e}")
            return False


# Global instance
release_service = ReleaseService()
