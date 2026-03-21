"""
C.O.V.E.R.T - Reputation Service

Implements the off-chain reputation system defined in docs/SYSTEM_SPEC.md.

Tiers (§2):
  Tier 0  Rep < 20
  Tier 1  20 – 79
  Tier 2  80 – 199
  Tier 3  ≥ 200

Rep changes are applied after a report is finalized (§4 / §9).
Slashing adds an extra -5 on top of any label-based delta (§5).
Strikes track bad actors within a rolling 30-day window (§6).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Set, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user_reputation import UserReputation

logger = logging.getLogger(__name__)

# ── Tier thresholds (spec §2) ─────────────────────────────────────────────────
# Ordered from highest to lowest so we can iterate and return the first match.
TIER_THRESHOLDS: list[tuple[str, int]] = [
    ('tier_3', 200),
    ('tier_2', 80),
    ('tier_1', 20),
    ('tier_0', 0),
]

# ── Rep deltas per FinalLabel (spec §4) ───────────────────────────────────────

REPORTER_REP_DELTA: Dict[str, int] = {
    'CORROBORATED':         8,
    'NEEDS_EVIDENCE':       0,
    'DISPUTED':            -2,
    'FALSE_OR_MANIPULATED': -10,
}

SUPPORTER_REP_DELTA: Dict[str, int] = {
    'CORROBORATED':         1,
    'FALSE_OR_MANIPULATED': -2,
    # All other labels → 0 (handled by .get default)
}

CHALLENGER_REP_DELTA: Dict[str, int] = {
    'FALSE_OR_MANIPULATED': 2,
    'DISPUTED':             2,
    'NEEDS_EVIDENCE':       1,
    'CORROBORATED':        -2,
}

# ── Appeal rep deltas (spec §4) ───────────────────────────────────────────────
APPEAL_REP_DELTA: Dict[str, int] = {
    'APPEAL_WON':     2,
    'APPEAL_LOST':    0,
    'APPEAL_ABUSIVE': -5,
}

# ── Constants ─────────────────────────────────────────────────────────────────
SLASH_PENALTY       = -5   # Additional rep loss per slashing event (spec §5)
MALICIOUS_PENALTY   = -5   # Rep penalty for explicit malicious flag (spec §4)
REVIEWER_APPEAL_WON_PENALTY = -5  # Reviewer penalized when appeal overturns their decision
STRIKE_WINDOW_DAYS  = 30
REVIEWER_REP_THRESHOLD   = 50
MODERATOR_REP_THRESHOLD  = 90
REVIEWER_ACCOUNT_AGE_DAYS = 30

# ── Dev / Test account seed config (mirrors frontend/src/config/roles.ts) ────
# Addresses are the standard Hardhat/Anvil accounts. Scores are set by
# role-threshold constants above — NOT hardcoded magic numbers per wallet.
DEV_TEST_ACCOUNTS: Dict[str, List[str]] = {
    'user': [
        '0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266',  # Account 0
        '0x70997970c51812dc3a010c7d01b50e0d17dc79c8',  # Account 1
        '0x9965507d1a55bcc2695c58ba16fb37d819b0a4dc',  # Account 5
        '0x14dc79964da2c08b23698b3d3cc7ca32193d9955',  # Account 7
        '0x23618e81e3f5cdf7f54c3d65f7fbc0abf5b21e8f',  # Account 8
    ],
    'reviewer': [
        '0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc',  # Account 2
        '0x15d34aaf54267db7d7c367839aaf71a00a2c6a65',  # Account 4
    ],
    'moderator': [
        '0x90f79bf6eb2c4f870365e785982e1f101e93b906',  # Account 3
        '0x976ea74026e726554db657fa54763abd0c3a0aa9',  # Account 6
        '0xa0ee7a142d267c1f36714e4a8f75612f20a79720',  # Account 9
    ],
}

# Maps role → initial rep score (derived from threshold constants, not magic numbers)
ROLE_INITIAL_SCORES: Dict[str, int] = {
    'user':      0,
    'reviewer':  REVIEWER_REP_THRESHOLD,   # 50 — minimum to qualify
    'moderator': MODERATOR_REP_THRESHOLD,  # 90 — minimum to qualify
}


class ReputationService:
    # ── Legacy constants kept for the /tiers endpoint ─────────────────────────
    BRONZE_THRESHOLD    = 0
    SILVER_THRESHOLD    = 100
    GOLD_THRESHOLD      = 500
    PLATINUM_THRESHOLD  = 1000
    ACCURATE_REVIEW_POINTS  = 10
    DISPUTED_REVIEW_PENALTY = 20
    DECAY_RATE          = 1
    DECAY_INTERVAL_DAYS = 7
    TIER_RATE_LIMITS    = {'bronze': 5, 'silver': 10, 'gold': 20, 'platinum': 50}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _calculate_tier(self, score: int) -> str:
        for tier, threshold in TIER_THRESHOLDS:
            if score >= threshold:
                return tier
        return 'tier_0'

    async def get_or_create(
        self, db: AsyncSession, wallet_address: str
    ) -> UserReputation:
        """Return existing UserReputation row, creating one on first encounter."""
        result = await db.execute(
            select(UserReputation).where(
                UserReputation.wallet_address.ilike(wallet_address)
            )
        )
        urep = result.scalar_one_or_none()
        if urep:
            return urep

        urep = UserReputation(
            wallet_address=wallet_address.lower(),
            reputation_score=0,
            tier='tier_0',
            strikes=0,
        )
        db.add(urep)
        await db.flush()
        return urep

    async def _apply_delta(
        self,
        db: AsyncSession,
        wallet_address: str,
        delta: int,
        slashed: bool = False,
        add_strike: bool = False,
    ) -> UserReputation:
        """Apply a reputation delta to a wallet, handling tier + strike tracking."""
        urep = await self.get_or_create(db, wallet_address)
        now = datetime.utcnow()

        new_score = max(0, urep.reputation_score + delta)
        urep.reputation_score = new_score
        urep.tier = self._calculate_tier(new_score)
        urep.updated_at = now

        if slashed:
            urep.last_slash_at = now
            logger.info(f"[rep] Slashed {wallet_address}: delta={delta}")

        if add_strike:
            window = now - timedelta(days=STRIKE_WINDOW_DAYS)
            # Reset counter when the previous strike window has expired
            if urep.last_strike_at and urep.last_strike_at < window:
                urep.strikes = 1
            else:
                urep.strikes = (urep.strikes or 0) + 1
            urep.last_strike_at = now
            logger.info(
                f"[rep] Strike #{urep.strikes} issued to {wallet_address}"
            )

        return urep

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_by_wallet(
        self, db: AsyncSession, wallet_address: str
    ) -> Dict[str, Any]:
        """Return reputation data for any wallet address (defaults to tier_0 / 0 for unknowns)."""
        result = await db.execute(
            select(UserReputation).where(
                UserReputation.wallet_address.ilike(wallet_address)
            )
        )
        urep = result.scalar_one_or_none()
        if not urep:
            return {
                "reputation_score": 0,
                "tier": "tier_0",
                "total_reviews": 0,
                "accuracy_rate": 0.0,
                "is_active": False,
            }
        return {
            "reputation_score": urep.reputation_score,
            "tier": urep.tier,
            "total_reviews": 0,
            "accuracy_rate": 0.0,
            "is_active": True,
        }

    async def apply_finalization_rep_changes(
        self,
        db: AsyncSession,
        reporter: str,
        final_label: str,
        appeal_outcome: Optional[str],
        supporters: List[str],
        challengers: List[str],
        malicious_set: Set[str],
    ) -> None:
        """
        Apply rep changes to all report participants when a report is finalized.

        Implements spec §4 (rep effects per action) and §5 (slashing rules).

        Args:
            reporter:       Wallet address of the original reporter.
            final_label:    One of CORROBORATED | NEEDS_EVIDENCE | DISPUTED | FALSE_OR_MANIPULATED.
            appeal_outcome: One of APPEAL_WON | APPEAL_LOST | APPEAL_ABUSIVE | None.
            supporters:     List of wallet addresses that staked in support.
            challengers:    List of wallet addresses that challenged the report.
            malicious_set:  Wallets explicitly marked malicious by a moderator.
        """

        # ── Reporter ──────────────────────────────────────────────────────────
        r_delta   = REPORTER_REP_DELTA.get(final_label, 0)
        r_slashed = False
        r_strike  = False

        # FALSE_OR_MANIPULATED triggers a slash (spec §5)
        if final_label == 'FALSE_OR_MANIPULATED':
            r_delta  += SLASH_PENALTY   # additional -5 on top of label-based -10
            r_slashed = True

        # Appeal effects (additive on top of finalization delta)
        if appeal_outcome:
            r_delta += APPEAL_REP_DELTA.get(appeal_outcome, 0)
            if appeal_outcome == 'APPEAL_ABUSIVE':
                r_slashed = True
                r_strike  = True

        # Explicit malicious flag from moderator (spec §4)
        if reporter in malicious_set:
            r_delta  += MALICIOUS_PENALTY
            r_strike  = True

        await self._apply_delta(
            db, reporter, r_delta,
            slashed=r_slashed, add_strike=r_strike,
        )

        # ── Supporters ────────────────────────────────────────────────────────
        s_base_delta   = SUPPORTER_REP_DELTA.get(final_label, 0)
        s_base_slashed = final_label == 'FALSE_OR_MANIPULATED'

        for supporter in supporters:
            s_delta   = s_base_delta
            s_slashed = s_base_slashed
            s_strike  = False

            if s_base_slashed:
                s_delta += SLASH_PENALTY   # additional -5 for supporters on FALSE_OR_MANIPULATED

            if supporter in malicious_set:
                s_delta  += MALICIOUS_PENALTY
                s_strike  = True

            await self._apply_delta(
                db, supporter, s_delta,
                slashed=s_slashed, add_strike=s_strike,
            )

        # ── Challengers ───────────────────────────────────────────────────────
        c_base_delta = CHALLENGER_REP_DELTA.get(final_label, 0)

        for challenger in challengers:
            c_delta  = c_base_delta
            c_strike = False

            if challenger in malicious_set:
                c_delta  += MALICIOUS_PENALTY
                c_strike  = True

            await self._apply_delta(
                db, challenger, c_delta,
                add_strike=c_strike,
            )

        await db.commit()
        logger.info(
            f"[rep] Finalization applied — label={final_label} "
            f"reporter={reporter} supporters={len(supporters)} "
            f"challengers={len(challengers)} malicious={len(malicious_set)}"
        )

    async def issue_strike(
        self, db: AsyncSession, wallet_address: str
    ) -> UserReputation:
        """Issue a standalone strike + slash penalty (e.g., moderator action). Spec §5 / §6."""
        urep = await self._apply_delta(
            db, wallet_address, MALICIOUS_PENALTY,
            slashed=True, add_strike=True,
        )
        await db.commit()
        return urep

    async def apply_reviewer_appeal_penalty(
        self, db: AsyncSession, reviewer_address: str
    ) -> None:
        """Penalize a reviewer when their decision is overturned by a successful appeal."""
        await self._apply_delta(
            db, reviewer_address, REVIEWER_APPEAL_WON_PENALTY,
            slashed=True,
        )
        await db.commit()
        logger.info(f"[rep] Reviewer appeal penalty applied to {reviewer_address}")

    async def count_active_strikes(
        self, db: AsyncSession, wallet_address: str
    ) -> int:
        """Return number of active strikes within the rolling 30-day window."""
        urep = await self.get_or_create(db, wallet_address)
        if not urep.last_strike_at:
            return 0
        window = datetime.utcnow() - timedelta(days=STRIKE_WINDOW_DAYS)
        if urep.last_strike_at < window:
            return 0
        return urep.strikes or 0

    async def check_reviewer_eligibility(
        self, db: AsyncSession, wallet_address: str
    ) -> Dict[str, Any]:
        """
        Check whether a wallet meets the Reviewer activation requirements (spec §3):
          • Rep ≥ 50
          • Account age ≥ 30 days
          • No slashing in the last 30 days
          • Fewer than 3 active strikes
        """
        urep = await self.get_or_create(db, wallet_address)
        now         = datetime.utcnow()
        window_start = now - timedelta(days=STRIKE_WINDOW_DAYS)

        rep_ok   = urep.reputation_score >= REVIEWER_REP_THRESHOLD
        age_ok   = (now - urep.account_created_at).days >= REVIEWER_ACCOUNT_AGE_DAYS
        slash_ok = (urep.last_slash_at is None) or (urep.last_slash_at < window_start)

        active_strikes = 0
        if urep.last_strike_at and urep.last_strike_at >= window_start:
            active_strikes = urep.strikes or 0
        strikes_ok = active_strikes < 3

        eligible = rep_ok and age_ok and slash_ok and strikes_ok

        return {
            "eligible":        eligible,
            "reputation_score": urep.reputation_score,
            "rep_ok":          rep_ok,
            "age_ok":          age_ok,
            "slash_ok":        slash_ok,
            "strikes_ok":      strikes_ok,
            "active_strikes":  active_strikes,
        }

    async def get_flagged_wallets(
        self,
        db: AsyncSession,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        """Return wallets with active strikes (within the rolling 30-day window)."""
        window_start = datetime.utcnow() - timedelta(days=STRIKE_WINDOW_DAYS)
        result = await db.execute(
            select(UserReputation)
            .where(
                UserReputation.strikes > 0,
                UserReputation.last_strike_at >= window_start,
            )
            .order_by(UserReputation.last_strike_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [
            {
                "wallet_address": urep.wallet_address,
                "reputation_score": urep.reputation_score,
                "tier": urep.tier,
                "strikes": urep.strikes,
                "last_strike_at": urep.last_strike_at.isoformat() if urep.last_strike_at else None,
                "last_slash_at": urep.last_slash_at.isoformat() if urep.last_slash_at else None,
            }
            for urep in rows
        ]

    async def get_reviewer_candidates(
        self,
        db: AsyncSession,
        limit: int = 20,
    ) -> list[Dict[str, Any]]:
        """Return top users by rep score (potential / active reviewers)."""
        result = await db.execute(
            select(UserReputation)
            .where(UserReputation.reputation_score >= REVIEWER_REP_THRESHOLD)
            .order_by(UserReputation.reputation_score.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        now = datetime.utcnow()
        window_start = now - timedelta(days=STRIKE_WINDOW_DAYS)
        return [
            {
                "wallet_address": urep.wallet_address,
                "reputation_score": urep.reputation_score,
                "tier": urep.tier,
                "account_age_days": (now - urep.account_created_at).days if urep.account_created_at else 0,
                "active_strikes": (urep.strikes or 0) if (urep.last_strike_at and urep.last_strike_at >= window_start) else 0,
                "slash_ok": (urep.last_slash_at is None) or (urep.last_slash_at < window_start),
            }
            for urep in rows
        ]

    # ── Leaderboard (using user_reputation table) ─────────────────────────────

    async def get_leaderboard(
        self,
        db: AsyncSession,
        limit: int = 10,
        tier_filter: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        query = select(UserReputation).order_by(
            UserReputation.reputation_score.desc()
        )
        if tier_filter:
            query = query.where(UserReputation.tier == tier_filter)
        query = query.limit(limit)

        result = await db.execute(query)
        rows   = result.scalars().all()

        return [
            {
                "rank":             i,
                "wallet_address":   urep.wallet_address[:10] + "...",
                "reputation_score": urep.reputation_score,
                "tier":             urep.tier,
                "total_reviews":    0,
                "accuracy_rate":    0.0,
            }
            for i, urep in enumerate(rows, 1)
        ]

    # ── Legacy moderator-specific methods (kept for /stats, /decay, /rate-limit) ──

    async def get_moderator_stats(
        self, db: AsyncSession, moderator_id: str
    ) -> Dict[str, Any]:
        from app.models.moderator import Moderator
        moderator = await db.get(Moderator, moderator_id)
        if not moderator:
            raise ValueError(f"Moderator {moderator_id} not found")

        accuracy_rate = 0.0
        if moderator.total_reviews > 0:
            accuracy_rate = (moderator.accurate_reviews / moderator.total_reviews) * 100

        rate_limit = self.TIER_RATE_LIMITS.get(moderator.tier, 5)
        return {
            "moderator_id":    str(moderator.id),
            "wallet_address":  moderator.wallet_address,
            "reputation_score": moderator.reputation_score,
            "tier":            moderator.tier,
            "total_reviews":   moderator.total_reviews,
            "accurate_reviews": moderator.accurate_reviews,
            "disputed_reviews": moderator.disputed_reviews,
            "accuracy_rate":   round(accuracy_rate, 2),
            "is_active":       moderator.is_active,
            "is_suspended":    moderator.is_suspended,
            "can_moderate":    moderator.can_moderate(),
            "daily_rate_limit": rate_limit,
            "last_active": (
                moderator.last_active_at.isoformat()
                if moderator.last_active_at else None
            ),
        }

    async def apply_decay(
        self, db: AsyncSession, moderator_id: str
    ):
        """Legacy endpoint stub — decay is not part of the new rep system."""
        from app.models.moderator import Moderator
        moderator = await db.get(Moderator, moderator_id)
        if not moderator:
            raise ValueError(f"Moderator {moderator_id} not found")
        return moderator

    async def calculate_rate_limit(
        self, db: AsyncSession, moderator_id: str
    ) -> int:
        """Legacy endpoint stub."""
        from app.models.moderator import Moderator
        moderator = await db.get(Moderator, moderator_id)
        if not moderator:
            return 5
        return self.TIER_RATE_LIMITS.get(moderator.tier, 5)

    # ── Dev / Test reset (development environment only) ───────────────────────

    async def seed_dev_accounts(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Delete and re-seed all test accounts with role-appropriate starting rep.

        Scores are determined by ROLE_INITIAL_SCORES which references the
        REVIEWER_REP_THRESHOLD / MODERATOR_REP_THRESHOLD constants — no
        per-wallet magic numbers.  Only call this in a development environment.
        """
        all_addresses = [
            addr
            for addrs in DEV_TEST_ACCOUNTS.values()
            for addr in addrs
        ]

        # Wipe existing rows for test wallets
        await db.execute(
            delete(UserReputation).where(
                UserReputation.wallet_address.in_(all_addresses)
            )
        )
        await db.flush()

        seeded = []
        for role, addresses in DEV_TEST_ACCOUNTS.items():
            score = ROLE_INITIAL_SCORES[role]
            tier  = self._calculate_tier(score)
            for addr in addresses:
                urep = UserReputation(
                    wallet_address=addr,
                    reputation_score=score,
                    tier=tier,
                    strikes=0,
                )
                db.add(urep)
                seeded.append({
                    'address': addr,
                    'role':    role,
                    'score':   score,
                    'tier':    tier,
                })

        await db.commit()
        logger.info(f"[rep] Dev reset: seeded {len(seeded)} test accounts")
        return {'seeded': seeded, 'count': len(seeded)}


reputation_service = ReputationService()
