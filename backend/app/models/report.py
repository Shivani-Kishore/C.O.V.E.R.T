"""
C.O.V.E.R.T - Report Database Models

SQLAlchemy models for reports, moderations, and audit logs
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    Text,
    DateTime,
    Numeric,
    ForeignKey,
    Index,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ===== Enums =====

class ReportStatus(str, Enum):
    """Report status values"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    ARCHIVED = "archived"


class ReportVisibility(str, Enum):
    """Report visibility options"""
    PRIVATE = "private"
    MODERATED = "moderated"
    PUBLIC = "public"


class RiskLevel(str, Enum):
    """AI-assessed risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationAction(str, Enum):
    """Moderation action types"""
    REVIEW_STARTED = "review_started"
    REQUEST_INFO = "request_info"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ModerationDecision(str, Enum):
    """Moderation decision types"""
    ACCEPT = "accept"
    REJECT = "reject"
    NEED_INFO = "need_info"
    ESCALATE = "escalate"


class LogEventType(str, Enum):
    """Audit log event types"""
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    ACCESSED = "accessed"
    MODIFIED = "modified"
    DELETED = "deleted"
    MODERATION_STARTED = "moderation_started"
    MODERATION_COMPLETED = "moderation_completed"
    DISPUTED = "disputed"
    RELEASED = "released"
    DMS_TRIGGERED = "dms_triggered"


# ===== Models =====

class Report(Base):
    """
    Primary table for storing encrypted whistleblower reports

    All sensitive content is stored encrypted on IPFS.
    This table only contains metadata and references.
    """
    __tablename__ = "reports"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Blockchain Integration
    commitment_hash = Column(String(66), nullable=False, unique=True, index=True)
    transaction_hash = Column(String(66), index=True)
    block_number = Column(BigInteger)
    chain_id = Column(Integer, nullable=False)

    # IPFS Storage
    ipfs_cid = Column(String(100), nullable=False, unique=True, index=True)
    ipfs_gateway_url = Column(Text)

    # Encrypted Metadata (stored on IPFS, not here)
    encrypted_category = Column(String(500))
    encrypted_title = Column(String(1000))
    encrypted_summary = Column(Text)
    encrypted_file_hash = Column(String(100))

    # Report Metadata
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(50))
    submission_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )

    # Privacy Settings
    visibility = Column(
        SQLEnum(ReportVisibility),
        nullable=False,
        default=ReportVisibility.MODERATED
    )
    anonymous = Column(Boolean, nullable=False, default=True)

    # Status Tracking
    status = Column(
        SQLEnum(ReportStatus),
        nullable=False,
        default=ReportStatus.PENDING,
        index=True
    )
    verification_score = Column(Numeric(3, 2))  # 0.00 - 1.00
    risk_level = Column(SQLEnum(RiskLevel))

    # Reporter Identity (Anonymous)
    reporter_nullifier = Column(String(66), unique=True, index=True)
    reporter_commitment = Column(String(66))
    burner_address = Column(String(42))

    # Temporal Protection
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now()
    )
    last_accessed_at = Column(DateTime(timezone=True))

    # Dead Man's Switch
    dms_enabled = Column(Boolean, default=False)
    dms_trigger_date = Column(DateTime(timezone=True))
    dms_released = Column(Boolean, default=False)

    # Soft Delete
    deleted_at = Column(DateTime(timezone=True))
    deletion_reason = Column(Text)

    # Relationships
    moderations = relationship(
        "Moderation",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    logs = relationship(
        "ReportLog",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    zkp_nullifier = relationship(
        "ZKPNullifier",
        back_populates="report",
        uselist=False
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "verification_score >= 0.00 AND verification_score <= 1.00",
            name="valid_score"
        ),
        CheckConstraint(
            "commitment_hash ~ '^0x[a-fA-F0-9]{64}$'",
            name="commitment_format"
        ),
        CheckConstraint(
            "chain_id IN (137, 42161, 80001, 421613, 31337)",
            name="valid_chain"
        ),
        Index("idx_reports_status_active", status, postgresql_where=(deleted_at.is_(None))),
        Index("idx_reports_dms", dms_trigger_date, postgresql_where=(dms_enabled.is_(True) & dms_released.is_(False))),
    )

    def __repr__(self):
        return f"<Report {self.id} status={self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "commitment_hash": self.commitment_hash,
            "ipfs_cid": self.ipfs_cid,
            "ipfs_gateway_url": self.ipfs_gateway_url,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "chain_id": self.chain_id,
            "status": self.status.value if self.status else None,
            "visibility": self.visibility.value if self.visibility else None,
            "verification_score": float(self.verification_score) if self.verification_score else None,
            "risk_level": self.risk_level.value if self.risk_level else None,
            "file_size": self.file_size,
            "submission_timestamp": self.submission_timestamp.isoformat() if self.submission_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Moderation(Base):
    """
    Tracks moderation actions and decisions
    """
    __tablename__ = "moderations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    moderator_id = Column(UUID(as_uuid=True), index=True)  # References moderators table

    # Moderation Action
    action = Column(SQLEnum(ModerationAction), nullable=False)
    decision = Column(SQLEnum(ModerationDecision))

    # Encrypted Notes
    encrypted_notes = Column(Text)
    notes_encryption_key_hash = Column(String(66))

    # AI-Assisted Fields
    ai_recommendation = Column(String(20))
    ai_confidence = Column(Numeric(3, 2))
    ai_flags = Column(JSONB, default=[])

    # Decision Reasoning
    rejection_reason = Column(Text)
    verification_evidence = Column(Text)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    completed_at = Column(DateTime(timezone=True))

    # Metrics
    time_spent_seconds = Column(Integer)

    # Relationships
    report = relationship("Report", back_populates="moderations")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "ai_confidence >= 0.00 AND ai_confidence <= 1.00",
            name="valid_ai_confidence"
        ),
        Index("idx_moderations_pending", completed_at, postgresql_where=(completed_at.is_(None))),
    )

    def __repr__(self):
        return f"<Moderation {self.id} action={self.action}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "report_id": str(self.report_id),
            "moderator_id": str(self.moderator_id) if self.moderator_id else None,
            "action": self.action.value if self.action else None,
            "decision": self.decision.value if self.decision else None,
            "ai_recommendation": self.ai_recommendation,
            "ai_confidence": float(self.ai_confidence) if self.ai_confidence else None,
            "ai_flags": self.ai_flags,
            "time_spent_seconds": self.time_spent_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ReportLog(Base):
    """
    Audit trail for all report-related events
    """
    __tablename__ = "report_logs"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Keys
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    actor_id = Column(UUID(as_uuid=True))  # Could be moderator_id or null for system

    # Event Details
    event_type = Column(SQLEnum(LogEventType), nullable=False, index=True)
    event_data = Column(JSONB)

    # Change Tracking
    old_value = Column(Text)
    new_value = Column(Text)
    field_changed = Column(String(100))

    # Context
    ip_address_hash = Column(String(64))
    user_agent_hash = Column(String(64))

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )

    # Relationships
    report = relationship("Report", back_populates="logs")

    def __repr__(self):
        return f"<ReportLog {self.id} event={self.event_type}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "report_id": str(self.report_id),
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "event_type": self.event_type.value if self.event_type else None,
            "event_data": self.event_data,
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Anchor(Base):
    """
    Daily Merkle root anchors for tamper-proof timestamping
    """
    __tablename__ = "anchors"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Blockchain Data
    merkle_root = Column(String(66), nullable=False, unique=True, index=True)
    transaction_hash = Column(String(66), nullable=False)
    block_number = Column(BigInteger, nullable=False)
    chain_id = Column(Integer, nullable=False)

    # Anchor Metadata
    anchor_date = Column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    report_count = Column(Integer, nullable=False, default=0)

    # Merkle Tree Data
    merkle_tree = Column(JSONB)
    leaf_hashes = Column(ARRAY(Text))

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    anchored_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Anchor {self.id} date={self.anchor_date}>"


class ZKPNullifier(Base):
    """
    Prevents double-reporting while maintaining anonymity
    """
    __tablename__ = "zkp_nullifiers"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # ZKP Data
    nullifier = Column(String(66), nullable=False, unique=True, index=True)
    commitment = Column(String(66), nullable=False, index=True)

    # Usage Tracking
    first_used_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    usage_count = Column(Integer, nullable=False, default=1)

    # Rate Limiting
    daily_report_count = Column(Integer, nullable=False, default=1)
    last_daily_reset = Column(DateTime(timezone=True), nullable=False, default=func.current_date())

    # Associated Report
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="SET NULL")
    )

    # Relationships
    report = relationship("Report", back_populates="zkp_nullifier")

    def __repr__(self):
        return f"<ZKPNullifier {self.id}>"
