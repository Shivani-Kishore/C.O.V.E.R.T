import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.moderator import Moderator
from app.models.moderation import Moderation

logger = logging.getLogger(__name__)


class ReputationService:
    BRONZE_THRESHOLD = 0
    SILVER_THRESHOLD = 100
    GOLD_THRESHOLD = 500
    PLATINUM_THRESHOLD = 1000

    ACCURATE_REVIEW_POINTS = 10
    DISPUTED_REVIEW_PENALTY = 20
    DECAY_RATE = 1
    DECAY_INTERVAL_DAYS = 7

    TIER_RATE_LIMITS = {
        'bronze': 5,
        'silver': 10,
        'gold': 20,
        'platinum': 50
    }

    def __init__(self):
        pass

    async def initialize_moderator_reputation(
        self,
        db: AsyncSession,
        moderator_id: str,
        wallet_address: str,
        initial_score: int = 0
    ) -> Moderator:
        moderator = await db.get(Moderator, moderator_id)

        if moderator:
            logger.warning(f"Moderator {moderator_id} already has reputation")
            return moderator

        tier = self._calculate_tier(initial_score)

        moderator = Moderator(
            id=moderator_id,
            wallet_address=wallet_address,
            reputation_score=initial_score,
            tier=tier,
            total_reviews=0,
            accurate_reviews=0,
            disputed_reviews=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(moderator)
        await db.commit()
        await db.refresh(moderator)

        logger.info(f"Initialized reputation for moderator {moderator_id} with tier {tier}")

        return moderator

    async def update_reputation_after_moderation(
        self,
        db: AsyncSession,
        moderator_id: str,
        was_accurate: bool,
        was_disputed: bool
    ) -> Moderator:
        moderator = await db.get(Moderator, moderator_id)

        if not moderator:
            raise ValueError(f"Moderator {moderator_id} not found")

        if not moderator.is_active:
            raise ValueError(f"Moderator {moderator_id} is not active")

        await self._apply_decay_if_needed(db, moderator)

        moderator.total_reviews += 1

        old_score = moderator.reputation_score

        if was_accurate:
            moderator.accurate_reviews += 1
            moderator.reputation_score += self.ACCURATE_REVIEW_POINTS

        if was_disputed:
            moderator.disputed_reviews += 1
            if moderator.reputation_score >= self.DISPUTED_REVIEW_PENALTY:
                moderator.reputation_score -= self.DISPUTED_REVIEW_PENALTY
            else:
                moderator.reputation_score = 0

        old_tier = moderator.tier
        new_tier = self._calculate_tier(moderator.reputation_score)

        if old_tier != new_tier:
            moderator.tier = new_tier
            logger.info(f"Moderator {moderator_id} tier changed from {old_tier} to {new_tier}")

        moderator.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(moderator)

        logger.info(
            f"Updated reputation for {moderator_id}: "
            f"score {old_score} -> {moderator.reputation_score}, "
            f"tier {moderator.tier}"
        )

        return moderator

    async def apply_decay(
        self,
        db: AsyncSession,
        moderator_id: str
    ) -> Moderator:
        moderator = await db.get(Moderator, moderator_id)

        if not moderator:
            raise ValueError(f"Moderator {moderator_id} not found")

        decay_applied = await self._apply_decay_if_needed(db, moderator)

        if decay_applied:
            await db.commit()
            await db.refresh(moderator)

        return moderator

    async def get_moderator_stats(
        self,
        db: AsyncSession,
        moderator_id: str
    ) -> Dict[str, Any]:
        moderator = await db.get(Moderator, moderator_id)

        if not moderator:
            raise ValueError(f"Moderator {moderator_id} not found")

        accuracy_rate = 0.0
        if moderator.total_reviews > 0:
            accuracy_rate = (moderator.accurate_reviews / moderator.total_reviews) * 100

        rate_limit = self.TIER_RATE_LIMITS.get(moderator.tier, 5)

        return {
            "moderator_id": str(moderator.id),
            "wallet_address": moderator.wallet_address,
            "reputation_score": moderator.reputation_score,
            "tier": moderator.tier,
            "total_reviews": moderator.total_reviews,
            "accurate_reviews": moderator.accurate_reviews,
            "disputed_reviews": moderator.disputed_reviews,
            "accuracy_rate": round(accuracy_rate, 2),
            "is_active": moderator.is_active,
            "is_suspended": moderator.is_suspended,
            "can_moderate": moderator.can_moderate(),
            "daily_rate_limit": rate_limit,
            "last_active": moderator.last_active_at.isoformat() if moderator.last_active_at else None
        }

    async def get_leaderboard(
        self,
        db: AsyncSession,
        limit: int = 10,
        tier_filter: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        query = select(Moderator).where(Moderator.is_active == True)

        if tier_filter:
            query = query.where(Moderator.tier == tier_filter)

        query = query.order_by(Moderator.reputation_score.desc()).limit(limit)

        result = await db.execute(query)
        moderators = result.scalars().all()

        leaderboard = []
        for i, moderator in enumerate(moderators, 1):
            accuracy_rate = 0.0
            if moderator.total_reviews > 0:
                accuracy_rate = (moderator.accurate_reviews / moderator.total_reviews) * 100

            leaderboard.append({
                "rank": i,
                "wallet_address": moderator.wallet_address[:10] + "...",
                "reputation_score": moderator.reputation_score,
                "tier": moderator.tier,
                "total_reviews": moderator.total_reviews,
                "accuracy_rate": round(accuracy_rate, 2)
            })

        return leaderboard

    def _calculate_tier(self, score: int) -> str:
        if score >= self.PLATINUM_THRESHOLD:
            return 'platinum'
        elif score >= self.GOLD_THRESHOLD:
            return 'gold'
        elif score >= self.SILVER_THRESHOLD:
            return 'silver'
        else:
            return 'bronze'

    async def _apply_decay_if_needed(
        self,
        db: AsyncSession,
        moderator: Moderator
    ) -> bool:
        if not moderator.updated_at:
            return False

        time_since_update = datetime.utcnow() - moderator.updated_at
        days_since_update = time_since_update.days

        if days_since_update >= self.DECAY_INTERVAL_DAYS:
            periods = days_since_update // self.DECAY_INTERVAL_DAYS
            decay_amount = periods * self.DECAY_RATE

            old_score = moderator.reputation_score
            old_tier = moderator.tier

            if moderator.reputation_score >= decay_amount:
                moderator.reputation_score -= decay_amount
            else:
                moderator.reputation_score = 0

            new_tier = self._calculate_tier(moderator.reputation_score)

            if old_tier != new_tier:
                moderator.tier = new_tier

            logger.info(
                f"Applied decay to moderator {moderator.id}: "
                f"{old_score} -> {moderator.reputation_score} "
                f"({periods} periods, -{decay_amount} points)"
            )

            return True

        return False

    async def calculate_rate_limit(
        self,
        db: AsyncSession,
        moderator_id: str
    ) -> int:
        moderator = await db.get(Moderator, moderator_id)

        if not moderator:
            return 5

        return self.TIER_RATE_LIMITS.get(moderator.tier, 5)


reputation_service = ReputationService()
