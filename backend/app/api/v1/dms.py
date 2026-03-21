"""
C.O.V.E.R.T - Dead Man's Switch API Endpoints

Endpoints for DMS configuration, check-in, and release
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.schemas.dms import (
    DMSCreate,
    DMSUpdate,
    DMSResponse,
    DMSCheckInRequest,
    DMSCheckInResponse,
    DMSReleaseRequest,
    DMSReleaseResponse,
    DMSCancelRequest,
    DMSCancelResponse,
    DMSEmergencyOverrideRequest,
    DMSEmergencyOverrideResponse,
    DMSStatusResponse,
    DMSStatistics,
    WatchdogStatusResponse,
    DMSReleaseLogsResponse,
    DMSReleaseLogResponse
)
from app.services.dms import dms_service, release_service, watchdog_service
from app.models.dms import DeadMansSwitch, DMSReleaseLog
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dms", tags=["Dead Man's Switch"])


@router.post("/create", response_model=DMSResponse)
async def create_dms(
    request: DMSCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Dead Man's Switch for a report

    Allows reporters to configure automated release if they become unreachable.

    Requirements:
    - Report must exist and belong to reporter (verified by nullifier)
    - Trigger date must be in the future
    - Only one DMS per report

    Returns:
    - DMS configuration
    """
    try:
        # Validate trigger date is in future
        if request.trigger_date <= datetime.utcnow():
            raise HTTPException(status_code=400, detail="Trigger date must be in the future")

        # Create DMS
        dms = await dms_service.create_dms(
            db,
            report_id=request.report_id,
            reporter_nullifier=request.reporter_nullifier,
            trigger_date=request.trigger_date,
            trigger_type=request.trigger_type,
            reporter_commitment=request.reporter_commitment,
            inactivity_days=request.inactivity_days,
            auto_release_public=request.auto_release_public,
            auto_pin_ipfs=request.auto_pin_ipfs,
            notify_contacts=request.notify_contacts,
            encrypted_contacts=request.encrypted_contacts
        )

        if not dms:
            raise HTTPException(status_code=400, detail="Failed to create DMS")

        return DMSResponse(**dms.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create DMS failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create DMS")


@router.post("/checkin", response_model=DMSCheckInResponse)
async def check_in(
    request: DMSCheckInRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check in to DMS to prevent trigger

    Reporter checks in to demonstrate they are still accessible,
    preventing automated release. Can optionally extend trigger date.

    Returns:
    - Check-in confirmation
    - Updated trigger date
    - Days until trigger
    """
    try:
        # Perform check-in
        check_in = await dms_service.check_in(
            db,
            dms_id=request.dms_id,
            reporter_nullifier=request.reporter_nullifier,
            proof_of_life=request.proof_of_life,
            zkp_proof=request.zkp_proof,
            extend_trigger_date=request.extend_trigger_date,
            extension_reason=request.extension_reason
        )

        if not check_in:
            raise HTTPException(status_code=400, detail="Check-in failed")

        # Get updated DMS
        dms = await db.execute(
            select(DeadMansSwitch).where(DeadMansSwitch.id == request.dms_id)
        )
        dms = dms.scalar_one_or_none()

        if not dms:
            raise HTTPException(status_code=404, detail="DMS not found")

        # Calculate days until trigger
        days_until = (dms.trigger_date - datetime.utcnow()).days

        return DMSCheckInResponse(
            success=True,
            dms_id=str(dms.id),
            check_in_timestamp=check_in.check_in_timestamp,
            next_trigger_date=dms.trigger_date,
            check_in_count=dms.check_in_count,
            days_until_trigger=max(0, days_until)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Check-in failed: {e}")
        raise HTTPException(status_code=500, detail="Check-in failed")


@router.post("/release", response_model=DMSReleaseResponse)
async def manual_release(
    request: DMSReleaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger DMS release

    Reporter can manually trigger report release before trigger date.

    Requires:
    - Valid reporter nullifier
    - ZKP proof (optional but recommended)

    Returns:
    - Release confirmation
    - Transaction hash
    - IPFS CID
    """
    try:
        # Verify ownership
        dms = await db.execute(
            select(DeadMansSwitch).where(
                DeadMansSwitch.id == request.dms_id,
                DeadMansSwitch.reporter_nullifier == request.reporter_nullifier
            )
        )
        dms = dms.scalar_one_or_none()

        if not dms:
            raise HTTPException(status_code=404, detail="DMS not found or unauthorized")

        # Trigger and release
        triggered = await release_service.trigger_dms(db, request.dms_id)
        if not triggered:
            raise HTTPException(status_code=400, detail="Failed to trigger DMS")

        result = await release_service.release_report(db, request.dms_id)

        if not result.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Release failed: {result.get('error', 'Unknown error')}"
            )

        # Get updated DMS
        await db.refresh(dms)

        return DMSReleaseResponse(
            success=True,
            dms_id=str(dms.id),
            report_id=str(dms.report_id),
            released_at=dms.released_at,
            release_transaction_hash=dms.release_transaction_hash,
            release_ipfs_cid=dms.release_ipfs_cid,
            notifications_sent=result.get('steps', [{}])[0].get('sent_count', 0) if result.get('steps') else 0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual release failed: {e}")
        raise HTTPException(status_code=500, detail="Release failed")


@router.post("/cancel", response_model=DMSCancelResponse)
async def cancel_dms(
    request: DMSCancelRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a Dead Man's Switch

    Reporter can cancel DMS to prevent automated release.

    Returns:
    - Cancellation confirmation
    """
    try:
        success = await dms_service.cancel_dms(
            db,
            dms_id=request.dms_id,
            reporter_nullifier=request.reporter_nullifier,
            reason=request.cancellation_reason
        )

        if not success:
            raise HTTPException(status_code=400, detail="Cancellation failed")

        return DMSCancelResponse(
            success=True,
            dms_id=request.dms_id,
            cancelled_at=datetime.utcnow(),
            message="DMS cancelled successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel DMS failed: {e}")
        raise HTTPException(status_code=500, detail="Cancellation failed")


@router.post("/emergency-override", response_model=DMSEmergencyOverrideResponse)
async def emergency_override(
    request: DMSEmergencyOverrideRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin emergency override of DMS

    Admin-only endpoint to override DMS behavior.

    Actions:
    - release: Force immediate release
    - cancel: Force cancellation
    - extend: Extend trigger date

    Requires admin authentication (wallet signature verification)
    """
    try:
        # TODO: Verify admin signature
        # verify_admin_signature(request.admin_wallet, signature)

        success = await release_service.emergency_override(
            db,
            dms_id=request.dms_id,
            admin_wallet=request.admin_wallet,
            action=request.override_action,
            reason=request.override_reason,
            extend_until=request.extend_until
        )

        if not success:
            raise HTTPException(status_code=400, detail="Emergency override failed")

        return DMSEmergencyOverrideResponse(
            success=True,
            dms_id=request.dms_id,
            action=request.override_action,
            override_at=datetime.utcnow(),
            override_by=request.admin_wallet
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emergency override failed: {e}")
        raise HTTPException(status_code=500, detail="Emergency override failed")


@router.get("/status/{dms_id}", response_model=DMSStatusResponse)
async def get_dms_status(
    dms_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get DMS status

    Returns current status, trigger date, and check-in information.
    """
    try:
        dms = await db.execute(
            select(DeadMansSwitch).where(DeadMansSwitch.id == dms_id)
        )
        dms = dms.scalar_one_or_none()

        if not dms:
            raise HTTPException(status_code=404, detail="DMS not found")

        # Calculate days until trigger
        days_until = (dms.trigger_date - datetime.utcnow()).days

        return DMSStatusResponse(
            id=str(dms.id),
            report_id=str(dms.report_id),
            status=dms.status.value,
            trigger_date=dms.trigger_date,
            days_until_trigger=max(0, days_until),
            last_check_in=dms.last_check_in,
            check_in_count=dms.check_in_count,
            release_attempts=dms.release_attempts,
            is_active=dms.status.value == 'active'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get DMS status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.get("/report/{report_id}", response_model=DMSResponse)
async def get_dms_by_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get DMS for a specific report"""
    try:
        dms = await dms_service.get_dms_by_report(db, report_id)

        if not dms:
            raise HTTPException(status_code=404, detail="DMS not found for report")

        return DMSResponse(**dms.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get DMS by report failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get DMS")


@router.get("/statistics", response_model=DMSStatistics)
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get DMS system statistics

    Returns counts and metrics for entire DMS system.
    """
    try:
        stats = await dms_service.get_dms_statistics(db)

        return DMSStatistics(
            total_active=stats.get('total_active', 0),
            total_triggered=stats.get('total_triggered', 0),
            total_released=stats.get('total_released', 0),
            total_cancelled=stats.get('total_cancelled', 0),
            pending_triggers_24h=stats.get('pending_triggers_24h', 0),
            pending_triggers_7d=stats.get('pending_triggers_7d', 0),
            avg_check_in_frequency_days=0.0,  # Would calculate from check-in history
            total_check_ins_today=stats.get('total_check_ins_today', 0),
            total_releases_today=stats.get('total_releases_today', 0)
        )

    except Exception as e:
        logger.error(f"Get statistics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/watchdog/status", response_model=WatchdogStatusResponse)
async def get_watchdog_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get watchdog service status

    Returns health and statistics of DMS watchdog service.
    """
    try:
        status = await watchdog_service.get_status(db)

        if status.get('status') == 'error':
            raise HTTPException(status_code=500, detail=status.get('error'))

        return WatchdogStatusResponse(
            service_name=status.get('service_name', 'dms_watchdog'),
            is_active=status.get('is_active', False),
            last_heartbeat=status.get('last_heartbeat', datetime.utcnow()),
            total_checks=status.get('total_checks', 0),
            triggers_found=status.get('triggers_found', 0),
            releases_attempted=status.get('releases_attempted', 0),
            releases_succeeded=status.get('releases_succeeded', 0),
            releases_failed=status.get('releases_failed', 0),
            avg_check_duration_ms=status.get('avg_check_duration_ms', 0),
            queue_size=status.get('queue_size', 0),
            check_interval_seconds=status.get('check_interval_seconds', 300)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get watchdog status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get watchdog status")


@router.post("/watchdog/manual-trigger")
async def manual_watchdog_trigger(
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger watchdog check (admin only)

    Forces an immediate check cycle for testing or emergency use.
    """
    try:
        result = await watchdog_service.manual_trigger_check(db)

        return {
            "success": True,
            "pending_count": result.get('pending_count', 0),
            "processed": result.get('processed', []),
            "duration_ms": result.get('duration_ms', 0)
        }

    except Exception as e:
        logger.error(f"Manual watchdog trigger failed: {e}")
        raise HTTPException(status_code=500, detail="Manual trigger failed")


@router.get("/logs/{dms_id}", response_model=DMSReleaseLogsResponse)
async def get_release_logs(
    dms_id: str,
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get release logs for a DMS

    Returns history of all release attempts and their outcomes.
    """
    try:
        # Get logs
        result = await db.execute(
            select(DMSReleaseLog)
            .where(DMSReleaseLog.dms_id == dms_id)
            .order_by(desc(DMSReleaseLog.attempt_timestamp))
            .limit(limit)
        )
        logs = list(result.scalars().all())

        # Convert to response format
        log_responses = [
            DMSReleaseLogResponse(
                id=log.id,
                dms_id=str(log.dms_id),
                attempt_number=log.attempt_number,
                attempt_timestamp=log.attempt_timestamp,
                action_type=log.action_type,
                action_success=log.action_success,
                transaction_hash=log.transaction_hash,
                ipfs_cid=log.ipfs_cid,
                error_message=log.error_message
            )
            for log in logs
        ]

        return DMSReleaseLogsResponse(
            dms_id=dms_id,
            total_logs=len(log_responses),
            logs=log_responses
        )

    except Exception as e:
        logger.error(f"Get release logs failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get logs")
