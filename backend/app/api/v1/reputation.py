from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.services.reputation_service import reputation_service
from pydantic import BaseModel

router = APIRouter(prefix="/reputation", tags=["Reputation"])


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


class LeaderboardEntry(BaseModel):
    rank: int
    wallet_address: str
    reputation_score: int
    tier: str
    total_reviews: int
    accuracy_rate: float


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
    if tier and tier not in ['bronze', 'silver', 'gold', 'platinum']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier. Must be bronze, silver, gold, or platinum"
        )

    leaderboard = await reputation_service.get_leaderboard(
        db,
        limit=min(limit, 100),
        tier_filter=tier
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
            "tier": moderator.tier
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
        "daily_limit": rate_limit
    }


@router.get("/tiers")
async def get_tier_thresholds():
    return {
        "tiers": [
            {
                "name": "bronze",
                "threshold": reputation_service.BRONZE_THRESHOLD,
                "rate_limit": reputation_service.TIER_RATE_LIMITS['bronze'],
                "color": "#CD7F32"
            },
            {
                "name": "silver",
                "threshold": reputation_service.SILVER_THRESHOLD,
                "rate_limit": reputation_service.TIER_RATE_LIMITS['silver'],
                "color": "#C0C0C0"
            },
            {
                "name": "gold",
                "threshold": reputation_service.GOLD_THRESHOLD,
                "rate_limit": reputation_service.TIER_RATE_LIMITS['gold'],
                "color": "#FFD700"
            },
            {
                "name": "platinum",
                "threshold": reputation_service.PLATINUM_THRESHOLD,
                "rate_limit": reputation_service.TIER_RATE_LIMITS['platinum'],
                "color": "#E5E4E2"
            }
        ],
        "scoring": {
            "accurate_review": reputation_service.ACCURATE_REVIEW_POINTS,
            "disputed_review": -reputation_service.DISPUTED_REVIEW_PENALTY,
            "decay_rate": reputation_service.DECAY_RATE,
            "decay_interval_days": reputation_service.DECAY_INTERVAL_DAYS
        }
    }
