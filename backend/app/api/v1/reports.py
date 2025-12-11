"""
C.O.V.E.R.T - Reports API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import hashlib

from app.core.database import get_db
from app.models.report import Report, ReportStatus, ReportVisibility
from app.services.report_service import report_service
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportListResponse,
    ReportListItem,
    ReportCommit,
)

router = APIRouter(prefix="/reports", tags=["reports"])


# Rate limiting store (use Redis in production)
RATE_LIMIT_STORE: dict = {}
MAX_REPORTS_PER_HOUR = 10


def check_rate_limit(identifier: str) -> bool:
    """Check if user has exceeded rate limit"""
    import time
    current_time = time.time()
    window_start = current_time - 3600  # 1 hour window

    if identifier not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[identifier] = []

    # Clean old entries
    RATE_LIMIT_STORE[identifier] = [
        t for t in RATE_LIMIT_STORE[identifier] if t > window_start
    ]

    if len(RATE_LIMIT_STORE[identifier]) >= MAX_REPORTS_PER_HOUR:
        return False

    RATE_LIMIT_STORE[identifier].append(current_time)
    return True


@router.post("", response_model=ReportResponse, status_code=201)
async def submit_report(
    report_data: ReportCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new encrypted report.

    The frontend has already:
    1. Encrypted the report client-side
    2. Uploaded to IPFS (got CID)
    3. Computed CID hash
    4. Committed to blockchain (got tx_hash)

    Backend indexes it in the database.
    """
    # Get identifier for rate limiting (wallet address or IP)
    identifier = request.headers.get("X-Wallet-Address", request.client.host if request.client else "unknown")

    # Check rate limit
    if not check_rate_limit(identifier):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {MAX_REPORTS_PER_HOUR} reports per hour"
        )

    # Validate CID format
    if not report_data.cid.startswith("bafy"):
        raise HTTPException(status_code=400, detail="Invalid IPFS CID format")

    # Validate transaction hash format
    if not report_data.tx_hash.startswith("0x") or len(report_data.tx_hash) != 66:
        raise HTTPException(status_code=400, detail="Invalid transaction hash format")

    # Verify CID hash matches
    computed_hash = hashlib.sha256(report_data.cid.encode()).hexdigest()
    cid_hash_clean = report_data.cid_hash.replace("0x", "")
    if computed_hash != cid_hash_clean:
        raise HTTPException(status_code=400, detail="CID hash mismatch")

    # Check for duplicate CID
    existing = await db.execute(
        select(Report).where(Report.cid == report_data.cid)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Report already submitted")

    # Create report
    try:
        report = await report_service.create_report(
            db=db,
            cid=report_data.cid,
            cid_hash=report_data.cid_hash,
            tx_hash=report_data.tx_hash,
            category=report_data.category,
            visibility=report_data.visibility,
            size_bytes=report_data.size_bytes,
            reporter_id=identifier,
        )

        return ReportResponse(
            id=str(report.id),
            cid=report.cid,
            cid_hash=report.cid_hash,
            tx_hash=report.tx_hash,
            category=report.category,
            status=report.status.value,
            visibility=report.visibility,
            size_bytes=report.size_bytes,
            submitted_at=report.submitted_at,
            message="Report submitted successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ReportListResponse)
async def list_reports(
    request: Request,
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's submitted reports with optional filtering.
    """
    identifier = request.headers.get("X-Wallet-Address", request.client.host if request.client else "unknown")

    reports, total = await report_service.get_user_reports(
        db=db,
        reporter_id=identifier,
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )

    items = [
        ReportListItem(
            id=str(r.id),
            cid=r.cid,
            cid_hash=r.cid_hash,
            tx_hash=r.tx_hash,
            category=r.category,
            status=r.status.value,
            visibility=r.visibility,
            size_bytes=r.size_bytes,
            verification_score=r.verification_score,
            risk_level=r.risk_level,
            submitted_at=r.submitted_at,
            reviewed_at=r.reviewed_at,
        )
        for r in reports
    ]

    return ReportListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get report details by ID.

    Note: Encrypted content is fetched from IPFS by the frontend.
    """
    identifier = request.headers.get("X-Wallet-Address", request.client.host if request.client else "unknown")

    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check ownership
    if report.reporter_id != identifier:
        raise HTTPException(status_code=403, detail="Access denied")

    return ReportResponse(
        id=str(report.id),
        cid=report.cid,
        cid_hash=report.cid_hash,
        tx_hash=report.tx_hash,
        category=report.category,
        status=report.status.value,
        visibility=report.visibility,
        size_bytes=report.size_bytes,
        verification_score=report.verification_score,
        risk_level=report.risk_level,
        submitted_at=report.submitted_at,
        reviewed_at=report.reviewed_at,
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a report as deleted (soft delete).

    Note: The blockchain commitment and IPFS data remain unchanged.
    """
    identifier = request.headers.get("X-Wallet-Address", request.client.host if request.client else "unknown")

    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_id != identifier:
        raise HTTPException(status_code=403, detail="Access denied")

    # Soft delete
    success = await report_service.delete_report(db, report_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete report")

    return {"message": "Report deleted successfully"}


@router.post("/{report_id}/commit", response_model=ReportResponse)
async def commit_to_blockchain(
    report_id: str,
    commit_data: ReportCommit,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Update report with blockchain commitment transaction hash.

    Called after the frontend successfully commits to the blockchain.
    """
    identifier = request.headers.get("X-Wallet-Address", request.client.host if request.client else "unknown")

    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_id != identifier:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update with blockchain info
    updated = await report_service.update_blockchain_info(
        db=db,
        report_id=report_id,
        tx_hash=commit_data.tx_hash,
        block_number=commit_data.block_number,
    )

    return ReportResponse(
        id=str(updated.id),
        cid=updated.cid,
        cid_hash=updated.cid_hash,
        tx_hash=updated.tx_hash,
        category=updated.category,
        status=updated.status.value,
        visibility=updated.visibility,
        size_bytes=updated.size_bytes,
        submitted_at=updated.submitted_at,
        message="Blockchain commitment recorded"
    )


@router.get("/{report_id}/status")
async def get_report_status(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current status of a report.
    """
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": str(report.id),
        "status": report.status.value,
        "verification_score": report.verification_score,
        "risk_level": report.risk_level,
        "reviewed_at": report.reviewed_at,
    }
