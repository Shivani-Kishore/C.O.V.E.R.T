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
import logging

logger = logging.getLogger(__name__)

# keccak256 for CID hash verification (matches ethers.keccak256 on the frontend)
try:
    from eth_hash.auto import keccak as keccak256_fn
except ImportError:
    try:
        from Crypto.Hash import keccak

        def keccak256_fn(data: bytes) -> bytes:  # type: ignore
            h = keccak.new(digest_bits=256)
            h.update(data)
            return h.digest()
    except ImportError as exc:
        raise ImportError(
            "Missing keccak256 backend. Install eth-hash[pycryptodome]."
        ) from exc

from app.core.database import get_db
from app.models.report import Report, ReportStatus, ReportVisibility
from app.services.report_service import report_service
from app.services.reputation_service import reputation_service
from app.api.v1.auth import get_current_wallet
from app.api.v1.rbac import require_reviewer_role, require_moderator_role
from app.core.config import settings
from pydantic import BaseModel as PydanticBaseModel

from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    ReportListResponse,
    ReportListItem,
    ReportCommit,
    ReportStatusUpdate,
)


class EvidenceKeyStore(PydanticBaseModel):
    """Body for storing an evidence AES key."""
    key_hex: str  # 64-char hex string (32-byte AES-256 key)


class FinalizeBody(PydanticBaseModel):
    """Body for finalizing a report — updates status and applies reputation changes."""
    status: str                              # 'verified' | 'rejected' | 'disputed' | 'under_review'
    final_label: Optional[str] = None       # 'CORROBORATED' | 'NEEDS_EVIDENCE' | 'DISPUTED' | 'FALSE_OR_MANIPULATED'
    reporter: Optional[str] = None          # reporter wallet address
    appeal_outcome: Optional[str] = None    # 'APPEAL_WON' | 'APPEAL_LOST' | 'APPEAL_ABUSIVE' | None
    supporters: Optional[List[str]] = None  # wallet addresses that supported
    challengers: Optional[List[str]] = None # wallet addresses that challenged
    malicious_wallets: Optional[List[str]] = None  # wallets marked malicious by moderator
    review_decision: Optional[str] = None   # 'REVIEW_PASSED' | 'NEEDS_EVIDENCE' | 'REJECT_SPAM' — reviewer's original decision

router = APIRouter(prefix="/reports", tags=["reports"])


# Import limiter lazily to avoid circular import (it's set on app.state in main.py)
def _get_limiter():
    from app.main import limiter
    return limiter


@router.post("", response_model=ReportResponse, status_code=201)
async def submit_report(
    report_data: ReportCreate,
    request: Request,
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a new encrypted report.

    Rate limited to RATE_LIMIT_SUBMISSIONS per hour (default: 10).
    The slowapi limiter on app.state handles enforcement via Redis.
    """
    identifier = wallet

    # Validate transaction hash format (tx_hash is optional — set later via /{id}/commit)
    if report_data.tx_hash and (not report_data.tx_hash.startswith("0x") or len(report_data.tx_hash) != 66):
        raise HTTPException(status_code=400, detail="Invalid transaction hash format")

    # Verify CID hash matches (frontend uses ethers.keccak256)
    cid_bytes = report_data.cid.encode('utf-8')
    computed_hash_bytes = keccak256_fn(cid_bytes)
    computed_hash_hex = computed_hash_bytes.hex()
    cid_hash_clean = report_data.cid_hash.lower().replace("0x", "")
    if computed_hash_hex != cid_hash_clean:
        raise HTTPException(status_code=400, detail="CID hash mismatch")

    # Check for duplicate CID
    existing = await db.execute(
        select(Report).where(Report.ipfs_cid == report_data.cid)
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
            title=report_data.title,
            description=report_data.description,
            delay_hours=report_data.delay_hours,
        )

        return ReportResponse(
            id=str(report.id),
            cid=report.ipfs_cid,
            cid_hash=report.commitment_hash,
            tx_hash=report.transaction_hash,
            category=report.encrypted_category,
            title=report.encrypted_title,
            description=report.encrypted_summary,
            status=report.status.value,
            visibility=report.visibility.value if hasattr(report.visibility, 'value') else str(report.visibility),
            size_bytes=report.file_size,
            submitted_at=report.submission_timestamp,
            scheduled_for=report.scheduled_for,
            message="Report submitted successfully"
        )

    except Exception as e:
        logger.error(f"Report submission failed: {e}")
        raise HTTPException(status_code=500, detail="Report submission failed")


@router.get("", response_model=ReportListResponse)
async def list_reports(
    request: Request,
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's submitted reports with optional filtering.
    """
    identifier = wallet

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
            cid=r.ipfs_cid,
            cid_hash=r.commitment_hash,
            tx_hash=r.transaction_hash,
            category=r.encrypted_category,
            title=r.encrypted_title,
            description=r.encrypted_summary,
            status=r.status.value,
            visibility=r.visibility.value if hasattr(r.visibility, 'value') else str(r.visibility),
            size_bytes=r.file_size,
            verification_score=float(r.verification_score) if r.verification_score else None,
            risk_level=r.risk_level.value if r.risk_level and hasattr(r.risk_level, 'value') else r.risk_level,
            submitted_at=r.submission_timestamp,
            reviewed_at=None,
            review_decision=r.review_decision,
            final_label=getattr(r, 'final_label', None),
        )
        for r in reports
    ]

    return ReportListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Static/non-parameterised routes MUST come before /{report_id} ──────────────

@router.get("/public", response_model=ReportListResponse)
async def list_public_reports(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List all public-visibility reports. No authentication required.
    Shown to all users on the reporter dashboard as a community feed.
    """
    reports, total = await report_service.get_public_reports(
        db=db,
        limit=limit,
        offset=offset,
        category=category,
    )

    items = [
        ReportListItem(
            id=str(r.id),
            cid=r.ipfs_cid,
            cid_hash=r.commitment_hash,
            tx_hash=r.transaction_hash or "0x" + "0" * 64,
            category=r.encrypted_category,
            title=r.encrypted_title,
            description=r.encrypted_summary,
            status=r.status.value,
            visibility=r.visibility.value if hasattr(r.visibility, 'value') else str(r.visibility),
            size_bytes=r.file_size,
            verification_score=float(r.verification_score) if r.verification_score else None,
            risk_level=r.risk_level.value if r.risk_level and hasattr(r.risk_level, 'value') else r.risk_level,
            submitted_at=r.submission_timestamp,
            reviewed_at=None,
            review_decision=r.review_decision,
            final_label=getattr(r, 'final_label', None),
        )
        for r in reports
    ]

    return ReportListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/all", response_model=ReportListResponse)
async def list_all_reports(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    wallet: str = Depends(require_reviewer_role),
    db: AsyncSession = Depends(get_db),
):
    """
    List ALL reports regardless of ownership.

    Used by reviewers and moderators to see the full report queue.
    Requires REVIEWER_ROLE or MODERATOR_ROLE on-chain.
    """
    reports, total = await report_service.get_all_reports(
        db=db,
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )

    items = [
        ReportListItem(
            id=str(r.id),
            cid=r.ipfs_cid,
            cid_hash=r.commitment_hash,
            tx_hash=r.transaction_hash or "0x" + "0" * 64,
            category=r.encrypted_category,
            title=r.encrypted_title,
            description=r.encrypted_summary,
            status=r.status.value,
            visibility=r.visibility.value if hasattr(r.visibility, 'value') else str(r.visibility),
            size_bytes=r.file_size,
            verification_score=float(r.verification_score) if r.verification_score else None,
            risk_level=r.risk_level.value if r.risk_level and hasattr(r.risk_level, 'value') else r.risk_level,
            submitted_at=r.submission_timestamp,
            reviewed_at=None,
            review_decision=r.review_decision,
            final_label=getattr(r, 'final_label', None),
        )
        for r in reports
    ]

    return ReportListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/by-hash/{cid_hash}", response_model=ReportResponse)
async def get_report_by_cid_hash(
    cid_hash: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch report metadata by CID hash (keccak256 of IPFS CID).

    Used by reviewers and moderators who know the on-chain contentHash but are
    not the original reporter. Returns title and description for review purposes.
    No ownership check — accessible to any authenticated reviewer/moderator in dev mode.
    """
    normalized = cid_hash.lower() if cid_hash.startswith("0x") else f"0x{cid_hash.lower()}"
    result = await db.execute(
        select(Report).where(Report.commitment_hash == normalized)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(
        id=str(report.id),
        cid=report.ipfs_cid,
        cid_hash=report.commitment_hash,
        tx_hash=report.transaction_hash or "0x" + "0" * 64,
        category=report.encrypted_category,
        title=report.encrypted_title,
        description=report.encrypted_summary,
        status=report.status.value,
        visibility=report.visibility.value if hasattr(report.visibility, 'value') else str(report.visibility),
        size_bytes=report.file_size,
        verification_score=float(report.verification_score) if report.verification_score else None,
        risk_level=report.risk_level.value if report.risk_level and hasattr(report.risk_level, 'value') else report.risk_level,
        submitted_at=report.submission_timestamp,
        reviewed_at=None,
    )


@router.patch("/by-hash/{cid_hash}/status")
async def update_report_status_by_hash(
    cid_hash: str,
    update: ReportStatusUpdate,
    wallet: str = Depends(require_reviewer_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Sync on-chain decision to backend DB status.

    Called by the frontend after setReviewDecision() or finalizeReport()
    succeeds on-chain so the reporter dashboard and public feed reflect
    the updated state without requiring a blockchain query.

    Allowed status values: under_review, verified, rejected, disputed, archived
    """
    normalized = cid_hash.lower() if cid_hash.startswith("0x") else f"0x{cid_hash.lower()}"
    result = await db.execute(
        select(Report).where(Report.commitment_hash == normalized)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        new_status = ReportStatus(update.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{update.status}'. Valid values: {[s.value for s in ReportStatus]}"
        )

    report.status = new_status
    if update.reviewer_address:
        report.reviewer_address = update.reviewer_address.lower()
    if update.review_decision:
        report.review_decision = update.review_decision
    await db.commit()

    return {"id": str(report.id), "status": report.status.value}


@router.post("/by-hash/{cid_hash}/finalize")
async def finalize_report(
    cid_hash: str,
    body: FinalizeBody,
    wallet: str = Depends(require_moderator_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the moderator frontend after a report is finalized (on-chain or DB-only mode).
    Updates the report status in the DB and applies reputation changes to all participants.
    """
    normalized = cid_hash.lower() if cid_hash.startswith("0x") else f"0x{cid_hash.lower()}"
    result = await db.execute(
        select(Report).where(Report.commitment_hash == normalized)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        new_status = ReportStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{body.status}'. Valid values: {[s.value for s in ReportStatus]}"
        )

    report.status = new_status
    if body.final_label:
        report.final_label = body.final_label
    if body.review_decision:
        report.review_decision = body.review_decision
    await db.commit()

    # Apply reputation changes when we have enough data to do so
    if body.final_label and body.reporter:
        await reputation_service.apply_finalization_rep_changes(
            db,
            reporter=body.reporter,
            final_label=body.final_label,
            appeal_outcome=body.appeal_outcome,
            supporters=body.supporters or [],
            challengers=body.challengers or [],
            malicious_set=set(body.malicious_wallets or []),
        )
        await db.commit()

    # ── Reviewer penalty: if moderator's final label contradicts the reviewer's decision ──
    # Matching logic:
    #   CORROBORATED         → expected REVIEW_PASSED
    #   FALSE_OR_MANIPULATED → expected REJECT_SPAM
    #   NEEDS_EVIDENCE/DISPUTED → expected NEEDS_EVIDENCE
    reviewer_addr = report.reviewer_address
    review_decision = body.review_decision
    if body.final_label and reviewer_addr and review_decision:
        DECISION_MATCH = {
            'CORROBORATED': 'REVIEW_PASSED',
            'FALSE_OR_MANIPULATED': 'REJECT_SPAM',
            'NEEDS_EVIDENCE': 'NEEDS_EVIDENCE',
            'DISPUTED': 'NEEDS_EVIDENCE',
        }
        expected_decision = DECISION_MATCH.get(body.final_label)
        if expected_decision and review_decision != expected_decision:
            # Mismatch — penalize the reviewer (−5 rep + strike)
            await reputation_service.issue_strike(db, reviewer_addr)

    # ── Reviewer penalty: appeal overturned the reviewer's decision ──
    if body.appeal_outcome == 'APPEAL_WON' and reviewer_addr:
        await reputation_service.apply_reviewer_appeal_penalty(db, reviewer_addr)

    # ── Route corroborated reports to civic departments ──
    if body.final_label == 'CORROBORATED':
        import asyncio
        from app.services.routing_service import route_report
        report_text = f"{report.encrypted_title or ''} {report.encrypted_summary or ''}"
        asyncio.create_task(route_report(str(report.id), report_text, db))

    return {"id": str(report.id), "status": report.status.value}


@router.post("/by-hash/{cid_hash}/resubmit")
async def resubmit_report(
    cid_hash: str,
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    Allow the reporter to resubmit a report that was returned by a reviewer.

    Valid for reports in 'needs_evidence' or 'rejected_by_reviewer' status.
    Resets status back to 'pending_review' and clears the review decision
    so it re-enters the reviewer queue from scratch.

    Only the original reporter may call this endpoint.
    """
    normalized = cid_hash.lower() if cid_hash.startswith("0x") else f"0x{cid_hash.lower()}"
    result = await db.execute(select(Report).where(Report.commitment_hash == normalized))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if (report.reporter_nullifier or "").lower() != wallet.lower():
        raise HTTPException(status_code=403, detail="Only the reporter may resubmit this report")

    allowed_statuses = {ReportStatus.NEEDS_EVIDENCE, ReportStatus.REJECTED_BY_REVIEWER}
    if report.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Resubmit not allowed for status '{report.status.value}'. "
                   f"Only 'needs_evidence' and 'rejected_by_reviewer' reports can be resubmitted."
        )

    report.status = ReportStatus.PENDING_REVIEW
    report.review_decision = None
    report.reviewer_address = None
    await db.commit()

    return {"id": str(report.id), "status": report.status.value, "message": "Report resubmitted for review"}


@router.post("/by-hash/{cid_hash}/evidence-key", status_code=200)
async def store_evidence_key(
    cid_hash: str,
    data: EvidenceKeyStore,
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    Store the AES-256 evidence key for a report (called by the reporter after submission).

    The key is stored for PUBLIC and MODERATED reports so reviewers/moderators
    can decrypt the IPFS blob in-browser. PRIVATE reports should not call this endpoint.
    Only the original reporter (matched by authenticated wallet) may store the key.
    """
    normalized = cid_hash.lower() if cid_hash.startswith("0x") else f"0x{cid_hash.lower()}"
    result = await db.execute(select(Report).where(Report.commitment_hash == normalized))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if (report.reporter_nullifier or "").lower() != wallet.lower():
        raise HTTPException(status_code=403, detail="Only the reporter can store the evidence key")

    if len(data.key_hex) != 64 or not all(c in "0123456789abcdefABCDEF" for c in data.key_hex):
        raise HTTPException(status_code=400, detail="key_hex must be a 64-character hex string")

    report.evidence_key = data.key_hex.lower()
    await db.commit()
    return {"stored": True}


@router.get("/by-hash/{cid_hash}/evidence-key")
async def get_evidence_key(
    cid_hash: str,
    wallet: str = Depends(require_reviewer_role),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the AES-256 evidence key for a report.

    Requires REVIEWER_ROLE or MODERATOR_ROLE on-chain.
    Returns 404 if no key has been stored (PRIVATE report or old submission).
    """
    normalized = cid_hash.lower() if cid_hash.startswith("0x") else f"0x{cid_hash.lower()}"
    result = await db.execute(select(Report).where(Report.commitment_hash == normalized))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.evidence_key:
        raise HTTPException(status_code=404, detail="No evidence key available for this report")
    return {
        "key_hex": report.evidence_key,
        "visibility": report.visibility.value if hasattr(report.visibility, 'value') else str(report.visibility),
    }


# ── Parameterised routes (must follow all static routes above) ─────────────────

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    Get report details by ID.

    Note: Encrypted content is fetched from IPFS by the frontend.
    """
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check ownership — use reporter_nullifier (authenticated wallet)
    if report.reporter_nullifier != wallet:
        raise HTTPException(status_code=403, detail="Access denied")

    return ReportResponse(
        id=str(report.id),
        cid=report.ipfs_cid,
        cid_hash=report.commitment_hash,
        tx_hash=report.transaction_hash,
        category=report.encrypted_category,
        title=report.encrypted_title,
        description=report.encrypted_summary,
        status=report.status.value,
        visibility=report.visibility.value if hasattr(report.visibility, 'value') else str(report.visibility),
        size_bytes=report.file_size,
        verification_score=float(report.verification_score) if report.verification_score else None,
        risk_level=report.risk_level.value if report.risk_level and hasattr(report.risk_level, 'value') else report.risk_level,
        submitted_at=report.submission_timestamp,
        reviewed_at=None,
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a report as deleted (soft delete).

    Note: The blockchain commitment and IPFS data remain unchanged.
    """
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_nullifier != wallet:
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
    wallet: str = Depends(get_current_wallet),
    db: AsyncSession = Depends(get_db),
):
    """
    Update report with blockchain commitment transaction hash.

    Called after the frontend successfully commits to the blockchain.
    """
    report = await report_service.get_report_by_id(db, report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_nullifier != wallet:
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
        cid=updated.ipfs_cid,
        cid_hash=updated.commitment_hash,
        tx_hash=updated.transaction_hash,
        category=updated.encrypted_category,
        status=updated.status.value,
        visibility=updated.visibility.value if hasattr(updated.visibility, 'value') else str(updated.visibility),
        size_bytes=updated.file_size,
        submitted_at=updated.submission_timestamp,
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
        "verification_score": float(report.verification_score) if report.verification_score else None,
        "risk_level": report.risk_level.value if report.risk_level and hasattr(report.risk_level, 'value') else report.risk_level,
        "reviewed_at": None,  # derive from moderation table if needed
    }
