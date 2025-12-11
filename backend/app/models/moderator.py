"""
C.O.V.E.R.T - Moderator Model
"""

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base


class Moderator(Base):
    """Moderator model with reputation tracking"""
    __tablename__ = "moderators"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Blockchain Identity
    wallet_address = Column(String(42), nullable=False, unique=True, index=True)
    reputation_token_id = Column(BigInteger, nullable=True)

    # Reputation Metrics
    reputation_score = Column(Integer, nullable=False, default=0, index=True)
    tier = Column(String(20), nullable=False, default='bronze', index=True)
    total_reviews = Column(Integer, nullable=False, default=0)
    accurate_reviews = Column(Integer, nullable=False, default=0)
    disputed_reviews = Column(Integer, nullable=False, default=0)

    # Activity Tracking
    last_active_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    suspension_until = Column(DateTime, nullable=True)
    suspension_reason = Column(Text, nullable=True)

    # Specialization
    expertise_areas = Column(JSONB, nullable=True)
    preferred_categories = Column(ARRAY(Text), nullable=True)

    # Performance Metrics
    average_review_time_seconds = Column(Integer, nullable=True)
    consistency_score = Column(Numeric(3, 2), nullable=True)

    # Privacy
    public_key = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    moderations = relationship("Moderation", back_populates="moderator")

    # Constraints
    __table_args__ = (
        CheckConstraint("tier IN ('bronze', 'silver', 'gold', 'platinum')", name='valid_tier'),
        CheckConstraint("wallet_address ~ '^0x[a-fA-F0-9]{40}$'", name='valid_address'),
        CheckConstraint('consistency_score >= 0.00 AND consistency_score <= 1.00', name='valid_consistency'),
    )

    def __repr__(self):
        return f"<Moderator {self.wallet_address} tier={self.tier} score={self.reputation_score}>"

    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate"""
        if self.total_reviews == 0:
            return 0.0
        return self.accurate_reviews / self.total_reviews

    @property
    def is_suspended(self) -> bool:
        """Check if moderator is currently suspended"""
        if not self.suspension_until:
            return False
        return datetime.utcnow() < self.suspension_until

    def can_moderate(self) -> bool:
        """Check if moderator can perform moderation"""
        return self.is_active and not self.is_suspended
