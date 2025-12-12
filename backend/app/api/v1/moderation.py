"""
C.O.V.E.R.T - Moderation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.services.moderation_service import moderation_service
from app.schemas.moderation import (
    ModerationQueueItem,
    ModerationDecisionCreate,
    ModerationResponse,
    ModerationHistoryItem,
    ModeratorStats,
    ModeratorCreate,
    ModeratorResponse,
    QueueSummary,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


# Simple auth check - in production, use proper JWT auth
def get_moderator_id(request: Request) -> str:
    """Extract moderator ID from request headers"""
    moderator_id = request.headers.get("X-Moderator-ID")
    if not moderator_id:
        raise HTTPException(status_code=401, detail="Moderator authentication required")
    return moderator_id


@router.get("/queue", response_model=List[ModerationQueueItem])
async def get_moderation_queue(
    request: Request,
    category: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get moderation queue

    Returns metadata only - NO encrypted content visible to moderators
    """
    moderator_id = get_moderator_id(request)

    reports, total = await moderation_service.get_moderation_queue(
        db=db,
        moderator_id=moderator_id,
        category=category,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )

    items = [
        ModerationQueueItem(
            id=str(r.id),
            cid=r.cid,
            cid_hash=r.cid_hash,
            category=r.category,
            status=r.status.value if hasattr(r.status, 'value') else r.status,
            visibility=r.visibility,
            size_bytes=r.size_bytes,
            verification_score=r.verification_score,
            risk_level=r.risk_level.value if r.risk_level and hasattr(r.risk_level, 'value') else r.risk_level,
            submitted_at=r.submitted_at,
        )
        for r in reports
    ]

    return items


@router.post("/review/start", response_model=ModerationResponse)
async def start_review(
    request: Request,
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Start reviewing a report"""
    moderator_id = get_moderator_id(request)

    moderation = await moderation_service.start_review(
        db=db,
        report_id=report_id,
        moderator_id=moderator_id,
    )

    if not moderation:
        raise HTTPException(status_code=404, detail="Report not found or already under review")

    return ModerationResponse(
        id=str(moderation.id),
        report_id=str(moderation.report_id),
        moderator_id=str(moderation.moderator_id) if moderation.moderator_id else None,
        action=moderation.action,
        decision=moderation.decision,
        created_at=moderation.created_at,
        completed_at=moderation.completed_at,
        time_spent_seconds=moderation.time_spent_seconds,
    )


@router.post("/review/submit", response_model=ModerationResponse)
async def submit_decision(
    request: Request,
    decision: ModerationDecisionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit moderation decision

    Decision types:
    - accept: Approve the report
    - reject: Reject the report
    - need_info: Request more information
    - escalate: Escalate to senior moderator
    """
    moderator_id = get_moderator_id(request)

    # Validate decision
    valid_decisions = ['accept', 'reject', 'need_info', 'escalate']
    if decision.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}"
        )

    moderation = await moderation_service.submit_decision(
        db=db,
        report_id=decision.report_id,
        moderator_id=moderator_id,
        decision=decision.decision,
        encrypted_notes=decision.encrypted_notes,
        rejection_reason=decision.rejection_reason,
        time_spent_seconds=decision.time_spent_seconds,
    )

    if not moderation:
        raise HTTPException(status_code=404, detail="Report not found")

    return ModerationResponse(
        id=str(moderation.id),
        report_id=str(moderation.report_id),
        moderator_id=str(moderation.moderator_id) if moderation.moderator_id else None,
        action=moderation.action,
        decision=moderation.decision,
        created_at=moderation.created_at,
        completed_at=moderation.completed_at,
        time_spent_seconds=moderation.time_spent_seconds,
    )


@router.get("/history", response_model=List[ModerationHistoryItem])
async def get_moderation_history(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get moderation history for current moderator"""
    moderator_id = get_moderator_id(request)

    moderations, total = await moderation_service.get_moderation_history(
        db=db,
        moderator_id=moderator_id,
        limit=limit,
        offset=offset,
    )

    items = [
        ModerationHistoryItem(
            id=str(m.id),
            report_id=str(m.report_id),
            action=m.action,
            decision=m.decision,
            created_at=m.created_at,
            completed_at=m.completed_at,
            time_spent_seconds=m.time_spent_seconds,
        )
        for m in moderations
    ]

    return items


@router.get("/stats", response_model=ModeratorStats)
async def get_moderator_stats(
    request: Request,
    period_days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get moderator statistics"""
    moderator_id = get_moderator_id(request)

    stats = await moderation_service.get_moderator_stats(
        db=db,
        moderator_id=moderator_id,
        period_days=period_days,
    )

    if not stats:
        raise HTTPException(status_code=404, detail="Moderator not found")

    return ModeratorStats(**stats)


@router.post("/register", response_model=ModeratorResponse, status_code=201)
async def register_moderator(
    moderator: ModeratorCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register as a moderator"""
    created = await moderation_service.create_or_update_moderator(
        db=db,
        wallet_address=moderator.wallet_address,
        public_key=moderator.public_key,
    )

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create moderator")

    return ModeratorResponse(
        id=str(created.id),
        wallet_address=created.wallet_address,
        reputation_score=created.reputation_score,
        tier=created.tier,
        total_reviews=created.total_reviews,
        is_active=created.is_active,
        created_at=created.created_at,
    )


@router.get("/queue/summary", response_model=QueueSummary)
async def get_queue_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get queue summary statistics"""
    from sqlalchemy import select, func
    from app.models.report import Report, ReportStatus
    from datetime import datetime, timedelta

    # Total pending
    total_result = await db.execute(
        select(func.count()).select_from(Report).where(
            Report.status == ReportStatus.PENDING
        )
    )
    total_pending = total_result.scalar() or 0

    # By risk level
    risk_counts = {}
    for risk in ['low', 'medium', 'high', 'critical']:
        result = await db.execute(
            select(func.count()).select_from(Report).where(
                Report.status == ReportStatus.PENDING,
                Report.risk_level == risk
            )
        )
        risk_counts[risk] = result.scalar() or 0

    # By category
    category_counts = {}
    for category in ['corruption', 'fraud', 'safety', 'environment', 'human_rights', 'other']:
        result = await db.execute(
            select(func.count()).select_from(Report).where(
                Report.status == ReportStatus.PENDING,
                Report.category == category
            )
        )
        category_counts[category] = result.scalar() or 0

    # Average wait time
    pending_reports = await db.execute(
        select(Report).where(Report.status == ReportStatus.PENDING)
    )
    pending_reports = list(pending_reports.scalars().all())

    if pending_reports:
        now = datetime.utcnow()
        wait_times = [(now - r.submitted_at).total_seconds() / 3600 for r in pending_reports]
        avg_wait = sum(wait_times) / len(wait_times)
        oldest_wait = max(wait_times)
    else:
        avg_wait = 0
        oldest_wait = 0

    return QueueSummary(
        total_pending=total_pending,
        by_risk_level=risk_counts,
        by_category=category_counts,
        average_wait_time_hours=round(avg_wait, 2),
        oldest_report_age_hours=round(oldest_wait, 2),
    )
