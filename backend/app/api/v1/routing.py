"""
C.O.V.E.R.T - Routing API Endpoints

Handles department routing, department responses, preview, and stats.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, extract
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.routing import Department, ReportRouting
from app.services.routing_service import get_report_routing
from app.services.classifier_service import classify_report, is_bangalore

router = APIRouter(prefix="/routing", tags=["routing"])


# ── Schemas ─────────────────────────────────────────────────────────────────

class DeptResponseUpdate(BaseModel):
    """Body for department response update."""
    status: str = Field(..., description="IN_PROGRESS | RESOLVED | NO_ACTION")
    response: Optional[str] = Field(None, max_length=500)


# ── 1. GET /routing/report/{report_id} — public ────────────────────────────

@router.get("/report/{report_id}")
async def get_routing_for_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all routing entries for a report (never exposes response_token)."""
    entries = await get_report_routing(str(report_id), db)
    return entries


# ── 2. GET /routing/dept-response/{token} — token is auth ──────────────────

@router.get("/dept-response/{token}")
async def get_dept_response(
    token: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Look up a routing entry by its unique response token."""
    result = await db.execute(
        select(ReportRouting, Department)
        .join(Department, ReportRouting.department_id == Department.id)
        .where(ReportRouting.response_token == token)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    routing, dept = row
    from app.core.config import settings
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")

    return {
        "dept_name": dept.name,
        "report_id": str(routing.report_id),
        "current_status": routing.status,
        "current_response": routing.department_response,
        "routed_at": routing.routed_at.isoformat() if routing.routed_at else None,
        "report_public_url": f"{frontend_url}/report/{routing.report_id}",
    }


# ── 3. PATCH /routing/dept-response/{token} — token is auth ────────────────

VALID_STATUSES = {"IN_PROGRESS", "RESOLVED", "NO_ACTION"}

@router.patch("/dept-response/{token}")
async def update_dept_response(
    token: UUID,
    body: DeptResponseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update department response status and optional public message."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    result = await db.execute(
        select(ReportRouting, Department)
        .join(Department, ReportRouting.department_id == Department.id)
        .where(ReportRouting.response_token == token)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")

    routing, dept = row

    # Guard: RESOLVED cannot revert to PENDING
    if routing.status == "RESOLVED" and body.status == "PENDING":
        raise HTTPException(status_code=400, detail="Cannot revert from RESOLVED to PENDING")

    routing.status = body.status
    if body.response is not None:
        routing.department_response = body.response
    routing.responded_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(routing)

    return {
        "dept_name": dept.name,
        "report_id": str(routing.report_id),
        "status": routing.status,
        "department_response": routing.department_response,
        "responded_at": routing.responded_at.isoformat() if routing.responded_at else None,
        "routed_at": routing.routed_at.isoformat() if routing.routed_at else None,
    }


# ── 4. GET /routing/preview?text=... — public, no DB write ─────────────────

@router.get("/preview")
async def routing_preview(
    text: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Classify text and return matching departments without writing to DB."""
    classification = classify_report(text)
    bangalore = is_bangalore(text)
    category = classification["category"]

    departments = []
    if bangalore and category != "other":
        dept_result = await db.execute(
            select(Department).where(
                and_(
                    Department.is_active.is_(True),
                    Department.categories.any(category),
                )
            )
        )
        for dept in dept_result.scalars().all():
            departments.append({
                "name": dept.name,
                "short_name": dept.short_name,
            })

    return {
        "is_bangalore": bangalore,
        "category": category,
        "matched_keywords": classification["matched_keywords"],
        "score": classification["score"],
        "departments": departments,
    }


# ── 5. GET /routing/stats — public, SQL aggregates ─────────────────────────

@router.get("/stats")
async def routing_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Per-department routing stats using SQL GROUP BY.
    Ordered by response_rate_percent descending.
    """
    # Per-department aggregates
    responded_case = case(
        (ReportRouting.responded_at.isnot(None), 1),
        else_=0,
    )
    resolved_case = case(
        (ReportRouting.status == "RESOLVED", 1),
        else_=0,
    )

    stmt = (
        select(
            Department.name.label("dept_name"),
            Department.short_name.label("short_name"),
            func.count(ReportRouting.id).label("total_routed"),
            func.sum(responded_case).label("total_responded"),
            func.sum(resolved_case).label("total_resolved"),
            func.max(ReportRouting.responded_at).label("last_responded_at"),
            func.avg(
                case(
                    (
                        ReportRouting.responded_at.isnot(None),
                        extract("epoch", ReportRouting.responded_at - ReportRouting.routed_at) / 86400.0,
                    ),
                    else_=None,
                )
            ).label("avg_response_days"),
        )
        .outerjoin(ReportRouting, Department.id == ReportRouting.department_id)
        .where(Department.is_active.is_(True))
        .group_by(Department.id, Department.name, Department.short_name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    departments = []
    total_routed_all = 0
    total_responded_all = 0
    fastest_dept = None
    fastest_days = None
    slowest_dept = None
    slowest_days = None

    for row in rows:
        total = row.total_routed or 0
        responded = row.total_responded or 0
        resolved = row.total_resolved or 0
        rate = round((responded / total * 100), 1) if total > 0 else 0.0
        avg_days = round(float(row.avg_response_days), 1) if row.avg_response_days else None

        total_routed_all += total
        total_responded_all += responded

        if avg_days is not None:
            if fastest_days is None or avg_days < fastest_days:
                fastest_days = avg_days
                fastest_dept = row.dept_name
            if slowest_days is None or avg_days > slowest_days:
                slowest_days = avg_days
                slowest_dept = row.dept_name

        departments.append({
            "dept_name": row.dept_name,
            "short_name": row.short_name,
            "total_routed": total,
            "total_responded": responded,
            "total_resolved": resolved,
            "response_rate_percent": rate,
            "avg_response_days": avg_days,
            "last_responded_at": row.last_responded_at.isoformat() if row.last_responded_at else None,
        })

    # Sort by response rate descending
    departments.sort(key=lambda d: d["response_rate_percent"], reverse=True)

    overall_rate = round((total_responded_all / total_routed_all * 100), 1) if total_routed_all > 0 else 0.0

    return {
        "summary": {
            "total_reports_routed": total_routed_all,
            "overall_response_rate_percent": overall_rate,
            "fastest_dept": fastest_dept,
            "slowest_dept": slowest_dept,
        },
        "departments": departments,
    }
