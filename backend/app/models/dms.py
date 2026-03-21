"""
C.O.V.E.R.T - Dead Man's Switch Models

Database models for automated report release system
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DMSStatus(str, Enum):
    """DMS status values"""
    ACTIVE = "active"              # Active, monitoring
    TRIGGERED = "triggered"        # Trigger date reached
    RELEASED = "released"          # Report released to public
    CANCELLED = "cancelled"        # DMS cancelled by reporter
    EXTENDED = "extended"          # Trigger date extended
    FAILED = "failed"              # Release failed


class DMSTriggerType(str, Enum):
    """DMS trigger types"""
    TIME_BASED = "time_based"      # Trigger after date
    ACTIVITY_BASED = "activity_based"  # Trigger after inactivity
    MANUAL = "manual"              # Manual trigger by reporter
    EMERGENCY = "emergency"        # Emergency admin trigger


class DeadMansSwitch(Base):
    """
    Dead Man's Switch configuration and status

    Automated report release when reporter becomes unreachable
    """
    __tablename__ = "dead_mans_switches"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Associated Report
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Reporter Identity (Anonymous)
    reporter_nullifier = Column(String(66), nullable=False, index=True)
    reporter_commitment = Column(String(66))

    # DMS Configuration
    trigger_type = Column(
        SQLEnum(DMSTriggerType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DMSTriggerType.TIME_BASED
    )
    trigger_date = Column(DateTime(timezone=True), nullable=False, index=True)
    inactivity_days = Column(Integer)  # For activity-based triggers

    # Status Tracking
    status = Column(
        SQLEnum(DMSStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DMSStatus.ACTIVE,
        index=True
    )
    last_check_in = Column(DateTime(timezone=True))
    check_in_count = Column(Integer, default=0)

    # Release Configuration
    auto_release_public = Column(Boolean, default=True)
    auto_pin_ipfs = Column(Boolean, default=True)
    notify_contacts = Column(Boolean, default=False)

    # Encrypted Contact Information
    encrypted_contacts = Column(JSONB)  # Encrypted email/contact list
    contacts_encryption_key_hash = Column(String(66))

    # Release History
    trigger_reached_at = Column(DateTime(timezone=True))
    released_at = Column(DateTime(timezone=True))
    release_transaction_hash = Column(String(66))
    release_ipfs_cid = Column(String(100))

    # Failure Tracking
    release_attempts = Column(Integer, default=0)
    last_release_attempt = Column(DateTime(timezone=True))
    failure_reason = Column(Text)

    # Emergency Override
    emergency_override = Column(Boolean, default=False)
    override_reason = Column(Text)
    override_by = Column(String(42))  # Admin wallet address
    override_at = Column(DateTime(timezone=True))

    # Timestamps
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
    cancelled_at = Column(DateTime(timezone=True))

    # Relationships
    report = relationship("Report", backref="dms")
    check_ins = relationship(
        "DMSCheckIn",
        back_populates="dms",
        cascade="all, delete-orphan"
    )
    release_logs = relationship(
        "DMSReleaseLog",
        back_populates="dms",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "inactivity_days IS NULL OR inactivity_days >= 1",
            name="valid_inactivity_days"
        ),
        Index(
            "idx_dms_active_triggers",
            trigger_date,
            postgresql_where=(
                (status == DMSStatus.ACTIVE) &
                (cancelled_at.is_(None))
            )
        ),
        Index(
            "idx_dms_pending_release",
            status,
            postgresql_where=(status == DMSStatus.TRIGGERED)
        ),
    )

    def __repr__(self):
        return f"<DeadMansSwitch {self.id} status={self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "report_id": str(self.report_id),
            "trigger_type": self.trigger_type.value if self.trigger_type else None,
            "trigger_date": self.trigger_date.isoformat() if self.trigger_date else None,
            "status": self.status.value if self.status else None,
            "last_check_in": self.last_check_in.isoformat() if self.last_check_in else None,
            "check_in_count": self.check_in_count,
            "auto_release_public": self.auto_release_public,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DMSCheckIn(Base):
    """
    Reporter check-in history

    Tracks when reporters check in to prevent DMS trigger
    """
    __tablename__ = "dms_check_ins"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Keys
    dms_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dead_mans_switches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Check-in Data
    check_in_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )
    proof_of_life = Column(String(200))  # Optional message/proof
    ip_address_hash = Column(String(64))
    user_agent_hash = Column(String(64))

    # ZKP Verification
    zkp_nullifier = Column(String(66))
    zkp_proof = Column(JSONB)

    # Extension
    extended_trigger_date = Column(DateTime(timezone=True))
    extension_reason = Column(Text)

    # Relationships
    dms = relationship("DeadMansSwitch", back_populates="check_ins")

    def __repr__(self):
        return f"<DMSCheckIn {self.id} at {self.check_in_timestamp}>"


class DMSReleaseLog(Base):
    """
    DMS release attempt and execution logs

    Tracks all release attempts, successes, and failures
    """
    __tablename__ = "dms_release_logs"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Keys
    dms_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dead_mans_switches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Release Data
    attempt_number = Column(Integer, nullable=False)
    attempt_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )

    # Release Actions
    action_type = Column(String(50), nullable=False)  # 'trigger', 'release', 'notify', 'pin'
    action_success = Column(Boolean, nullable=False)
    action_details = Column(JSONB)

    # Blockchain Data
    transaction_hash = Column(String(66))
    block_number = Column(BigInteger)
    gas_used = Column(BigInteger)

    # IPFS Data
    ipfs_cid = Column(String(100))
    ipfs_gateway_url = Column(Text)
    pin_status = Column(String(20))  # 'pinned', 'unpinned', 'failed'

    # Notification Data
    notifications_sent = Column(Integer, default=0)
    notification_status = Column(JSONB)

    # Error Tracking
    error_message = Column(Text)
    error_code = Column(String(50))
    stack_trace = Column(Text)

    # Retry Information
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime(timezone=True))

    # Relationships
    dms = relationship("DeadMansSwitch", back_populates="release_logs")

    def __repr__(self):
        return f"<DMSReleaseLog {self.id} attempt={self.attempt_number}>"


class DMSWatchdog(Base):
    """
    Watchdog service health monitoring

    Tracks watchdog service status and health checks
    """
    __tablename__ = "dms_watchdog"

    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Service Status
    service_name = Column(String(100), nullable=False, default="dms_watchdog")
    is_active = Column(Boolean, nullable=False, default=True)
    last_heartbeat = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )

    # Check Statistics
    total_checks = Column(BigInteger, default=0)
    triggers_found = Column(Integer, default=0)
    releases_attempted = Column(Integer, default=0)
    releases_succeeded = Column(Integer, default=0)
    releases_failed = Column(Integer, default=0)

    # Performance Metrics
    avg_check_duration_ms = Column(Integer)
    last_check_duration_ms = Column(Integer)
    queue_size = Column(Integer, default=0)

    # Error Tracking
    last_error = Column(Text)
    last_error_at = Column(DateTime(timezone=True))
    consecutive_errors = Column(Integer, default=0)

    # Configuration
    check_interval_seconds = Column(Integer, default=300)  # 5 minutes
    batch_size = Column(Integer, default=100)

    # Timestamps
    started_at = Column(DateTime(timezone=True), default=func.now())
    stopped_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<DMSWatchdog {self.service_name} active={self.is_active}>"
