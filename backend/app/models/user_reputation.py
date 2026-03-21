"""
C.O.V.E.R.T - UserReputation Model

Tracks reputation and tier for every wallet that interacts with the protocol.
Moderators/reviewers also have a row here (in addition to the moderators table).
"""

from sqlalchemy import Column, String, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class UserReputation(Base):
    __tablename__ = "user_reputation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identity
    wallet_address = Column(String(42), nullable=False, unique=True, index=True)

    # Rep & Tier  (spec §2)
    reputation_score = Column(Integer, nullable=False, default=0, index=True)
    tier = Column(String(20), nullable=False, default='tier_0', index=True)

    # Strike tracking  (spec §6)
    strikes = Column(Integer, nullable=False, default=0)
    last_strike_at = Column(DateTime, nullable=True)

    # Slash tracking  (used for reviewer eligibility gate)
    last_slash_at = Column(DateTime, nullable=True)

    # Account age gate (reviewer eligibility)
    account_created_at = Column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "wallet_address ~ '^0x[a-fA-F0-9]{40}$'",
            name='urep_valid_address',
        ),
        CheckConstraint(
            "tier IN ('tier_0','tier_1','tier_2','tier_3')",
            name='urep_valid_tier',
        ),
        CheckConstraint(
            "reputation_score >= 0",
            name='urep_non_negative_score',
        ),
    )

    def __repr__(self):
        return (
            f"<UserReputation {self.wallet_address} "
            f"score={self.reputation_score} tier={self.tier}>"
        )
