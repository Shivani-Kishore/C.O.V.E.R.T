from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from app.core.database import get_db
from app.schemas.zkp import (
    ZKProofSubmission,
    ZKProofVerificationResponse,
    ZKPRateLimitResponse,
)
from app.services.zkp.verifier import ZKProofVerifier
from app.models.report import ZKPNullifier

router = APIRouter(prefix="/zkp", tags=["ZKP"])

zkp_verifier = ZKProofVerifier()


@router.post("/verify", response_model=ZKProofVerificationResponse)
async def verify_zkp(
    proof_submission: ZKProofSubmission,
    db: AsyncSession = Depends(get_db),
):
    proof_dict = proof_submission.proof.model_dump()
    public_signals = proof_submission.public_signals

    result = await zkp_verifier.verify_proof(proof_dict, public_signals)

    if not result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Invalid proof"
        )

    return ZKProofVerificationResponse(
        is_valid=result.is_valid,
        commitment=result.commitment,
        nullifier_hash=result.nullifier_hash,
    )


@router.post("/check-nullifier", response_model=Dict[str, bool])
async def check_nullifier_uniqueness(
    nullifier: str,
    db: AsyncSession = Depends(get_db),
):
    is_unique = zkp_verifier.verify_nullifier_uniqueness(nullifier, db)

    return {
        "is_unique": is_unique,
        "can_submit": is_unique
    }


@router.get("/rate-limit/{nullifier}", response_model=ZKPRateLimitResponse)
async def check_rate_limit(
    nullifier: str,
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta

    within_limit = zkp_verifier.check_rate_limit(nullifier, db)

    nullifier_record = db.query(ZKPNullifier).filter_by(nullifier=nullifier).first()

    if nullifier_record:
        current_count = nullifier_record.daily_report_count
        last_reset = nullifier_record.last_daily_reset
    else:
        current_count = 0
        last_reset = datetime.now()

    reset_at = last_reset + timedelta(days=1)

    return ZKPRateLimitResponse(
        allowed=within_limit,
        current_count=current_count,
        limit=5,
        reset_at=reset_at
    )


@router.post("/submit-nullifier")
async def submit_nullifier(
    nullifier: str,
    commitment: str,
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.models.report import ZKPNullifier
    import uuid

    existing = db.query(ZKPNullifier).filter_by(nullifier=nullifier).first()

    if existing:
        existing.increment_usage()
        existing.report_id = uuid.UUID(report_id)
    else:
        new_nullifier = ZKPNullifier(
            nullifier=nullifier,
            commitment=commitment,
            report_id=uuid.UUID(report_id)
        )
        db.add(new_nullifier)

    db.commit()

    return {"success": True, "message": "Nullifier recorded"}


@router.get("/health")
async def zkp_health_check():
    has_vkey = zkp_verifier.verification_key is not None

    return {
        "status": "healthy" if has_vkey else "degraded",
        "verification_key_loaded": has_vkey,
        "message": "ZKP verification service operational" if has_vkey else "Verification key not loaded. Run circuit setup."
    }
