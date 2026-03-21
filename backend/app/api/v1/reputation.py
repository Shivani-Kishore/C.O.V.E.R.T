import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.services.reputation_service import reputation_service
from app.services.blockchain_service import blockchain_service
from app.api.v1.rbac import require_moderator_role
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reputation", tags=["Reputation"])

VALID_TIERS = {'tier_0', 'tier_1', 'tier_2', 'tier_3'}


class ReputationStats(BaseModel):
    moderator_id: str
    wallet_address: str
    reputation_score: int
    tier: str
    total_reviews: int
    accurate_reviews: int
    disputed_reviews: int
    accuracy_rate: float
    is_active: bool
    is_suspended: bool
    can_moderate: bool
    daily_rate_limit: int
    last_active: Optional[str] = None


class WalletReputation(BaseModel):
    reputation_score: int
    tier: str
    total_reviews: int
    accuracy_rate: float
    is_active: bool


class LeaderboardEntry(BaseModel):
    rank: int
    wallet_address: str
    reputation_score: int
    tier: str
    total_reviews: int
    accuracy_rate: float


class ReviewerEligibility(BaseModel):
    eligible: bool
    reputation_score: int
    rep_ok: bool
    age_ok: bool
    slash_ok: bool
    strikes_ok: bool
    active_strikes: int


@router.get("/wallet/{wallet_address}", response_model=WalletReputation)
async def get_reputation_by_wallet(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
):
    """Get reputation for any wallet address. Returns tier_0 / 0 defaults for unknown wallets."""
    return await reputation_service.get_by_wallet(db, wallet_address)


@router.get("/reviewer-eligibility/{wallet_address}", response_model=ReviewerEligibility)
async def get_reviewer_eligibility(
    wallet_address: str,
    db: AsyncSession = Depends(get_db),
):
    """Check whether a wallet meets the Reviewer activation requirements (spec §3)."""
    return await reputation_service.check_reviewer_eligibility(db, wallet_address)


@router.get("/stats/{moderator_id}", response_model=ReputationStats)
async def get_moderator_reputation(
    moderator_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        stats = await reputation_service.get_moderator_stats(db, moderator_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    limit: int = 10,
    tier: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if tier and tier not in VALID_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {', '.join(sorted(VALID_TIERS))}"
        )

    leaderboard = await reputation_service.get_leaderboard(
        db,
        limit=min(limit, 100),
        tier_filter=tier,
    )
    return leaderboard


@router.post("/decay/{moderator_id}")
async def apply_reputation_decay(
    moderator_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        moderator = await reputation_service.apply_decay(db, moderator_id)
        return {
            "success": True,
            "moderator_id": str(moderator.id),
            "new_score": moderator.reputation_score,
            "tier": moderator.tier,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/rate-limit/{moderator_id}")
async def get_rate_limit(
    moderator_id: str,
    db: AsyncSession = Depends(get_db),
):
    rate_limit = await reputation_service.calculate_rate_limit(db, moderator_id)
    return {
        "moderator_id": moderator_id,
        "daily_limit": rate_limit,
    }


class FlaggedUser(BaseModel):
    wallet_address: str
    reputation_score: int
    tier: str
    strikes: int
    last_strike_at: Optional[str] = None
    last_slash_at: Optional[str] = None


class ReviewerCandidate(BaseModel):
    wallet_address: str
    reputation_score: int
    tier: str
    account_age_days: int
    active_strikes: int
    slash_ok: bool


@router.get("/flagged", response_model=list[FlaggedUser])
async def get_flagged_wallets(
    limit: int = 50,
    wallet: str = Depends(require_moderator_role),
    db: AsyncSession = Depends(get_db),
):
    """Return wallets with active strikes within the rolling 30-day window."""
    return await reputation_service.get_flagged_wallets(db, limit=min(limit, 200))


@router.get("/reviewer-candidates", response_model=list[ReviewerCandidate])
async def get_reviewer_candidates(
    limit: int = 20,
    wallet: str = Depends(require_moderator_role),
    db: AsyncSession = Depends(get_db),
):
    """Return high-rep users who meet (or nearly meet) the Reviewer eligibility bar."""
    return await reputation_service.get_reviewer_candidates(db, limit=min(limit, 100))


@router.post("/dev-reset")
async def dev_reset_reputation(
    db: AsyncSession = Depends(get_db),
):
    """
    Reset and re-seed test account reputation scores based on role thresholds.
    Only available when ENVIRONMENT=development or DEBUG=true.
    """
    if not (settings.DEBUG and settings.ENVIRONMENT == "development"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode.",
        )
    result = await reputation_service.seed_dev_accounts(db)
    return {
        "success": True,
        "message": f"Seeded {result['count']} test accounts",
        "accounts": result["seeded"],
    }


@router.get("/tiers")
async def get_tier_thresholds():
    """Return tier thresholds as defined in spec §2."""
    return {
        "tiers": [
            {"name": "tier_0", "min_rep": 0,   "max_rep": 19,  "label": "Tier 0 — Low trust"},
            {"name": "tier_1", "min_rep": 20,  "max_rep": 79,  "label": "Tier 1 — Stable user"},
            {"name": "tier_2", "min_rep": 80,  "max_rep": 199, "label": "Tier 2 — High credibility"},
            {"name": "tier_3", "min_rep": 200, "max_rep": None, "label": "Tier 3 — Senior community"},
        ],
        "reviewer_eligibility": {
            "min_rep": 50,
            "min_account_age_days": 30,
            "no_slash_within_days": 30,
            "max_strikes_in_window": 2,
        },
        "rep_effects": {
            "reporter": {
                "CORROBORATED": 8,
                "NEEDS_EVIDENCE": 0,
                "DISPUTED": -2,
                "FALSE_OR_MANIPULATED": -10,
            },
            "supporter": {
                "CORROBORATED": 1,
                "FALSE_OR_MANIPULATED": -2,
                "others": 0,
            },
            "challenger": {
                "FALSE_OR_MANIPULATED": 2,
                "DISPUTED": 2,
                "NEEDS_EVIDENCE": 1,
                "CORROBORATED": -2,
            },
            "slash_penalty": -5,
            "malicious_penalty": -5,
        },
    }


@router.post("/sync-reviewer-roles")
async def sync_reviewer_roles(
    db: AsyncSession = Depends(get_db),
):
    """
    Scan all wallets and auto-grant/revoke REVIEWER_ROLE on-chain based on
    rep eligibility. Requires AUTOMATION_PRIVATE_KEY and COVERT_PROTOCOL_ADDRESS.
    """
    if not settings.AUTOMATION_PRIVATE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AUTOMATION_PRIVATE_KEY not configured",
        )
    if not settings.COVERT_PROTOCOL_ADDRESS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="COVERT_PROTOCOL_ADDRESS not configured",
        )

    # Ensure blockchain service is initialized
    if not blockchain_service.w3:
        await blockchain_service.initialize()

    candidates = await reputation_service.get_reviewer_candidates(db, limit=100)

    granted = []
    revoked = []
    errors = []

    for candidate in candidates:
        wallet = candidate["wallet_address"]
        eligibility = await reputation_service.check_reviewer_eligibility(db, wallet)
        has_role = await blockchain_service.has_reviewer_role(wallet)

        try:
            if eligibility["eligible"] and not has_role:
                await blockchain_service.grant_reviewer_role(wallet)
                granted.append(wallet)
                logger.info(f"[sync] Granted REVIEWER_ROLE to {wallet}")
            elif not eligibility["eligible"] and has_role:
                await blockchain_service.revoke_reviewer_role(wallet)
                revoked.append(wallet)
                logger.info(f"[sync] Revoked REVIEWER_ROLE from {wallet}")
        except Exception as e:
            errors.append({"wallet": wallet, "error": "role sync failed"})
            logger.error(f"[sync] Failed for {wallet}: {e}")

    return {
        "success": True,
        "granted": granted,
        "revoked": revoked,
        "errors": errors,
        "scanned": len(candidates),
    }
