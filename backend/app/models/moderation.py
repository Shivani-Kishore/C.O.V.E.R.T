"""
C.O.V.E.R.T - Moderation Model
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.database import Base


class Moderation(Base):
    """Moderation action model"""
    __tablename__ = "moderations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), nullable=False, index=True)
    moderator_id = Column(UUID(as_uuid=True), ForeignKey('moderators.id', ondelete='SET NULL'), nullable=True, index=True)

    # Moderation Action
    action = Column(String(50), nullable=False, index=True)
    decision = Column(String(20), nullable=True)

    # Encrypted Notes (only moderator can decrypt)
    encrypted_notes = Column(Text, nullable=True)
    notes_encryption_key_hash = Column(String(66), nullable=True)

    # AI-Assisted Fields
    ai_recommendation = Column(String(20), nullable=True)
    ai_confidence = Column(Numeric(3, 2), nullable=True)
    ai_flags = Column(JSONB, nullable=True)

    # Decision Reasoning
    rejection_reason = Column(Text, nullable=True)
    verification_evidence = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    completed_at = Column(DateTime, nullable=True)

    # Moderation Metrics
    time_spent_seconds = Column(Integer, nullable=True)

    # Relationships
    report = relationship("Report", back_populates="moderations")
    moderator = relationship("Moderator", back_populates="moderations")

    # Constraints
    __table_args__ = (
        CheckConstraint("action IN ('review_started', 'request_info', 'verified', 'rejected', 'escalated')", name='valid_action'),
        CheckConstraint("decision IN ('accept', 'reject', 'need_info', 'escalate') OR decision IS NULL", name='valid_decision'),
        CheckConstraint('ai_confidence >= 0.00 AND ai_confidence <= 1.00', name='valid_ai_confidence'),
    )

    def __repr__(self):
        return f"<Moderation {self.id} action={self.action} decision={self.decision}>"

    @property
    def is_completed(self) -> bool:
        """Check if moderation is completed"""
        return self.completed_at is not None

    @property
    def review_time_minutes(self) -> float:
        """Get review time in minutes"""
        if not self.time_spent_seconds:
            return 0.0
        return self.time_spent_seconds / 60.0
