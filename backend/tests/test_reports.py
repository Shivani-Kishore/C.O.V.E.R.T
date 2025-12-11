"""
C.O.V.E.R.T - Report Model and Database Tests

Tests for report models, database operations, and data integrity
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.report import (
    Report,
    Moderation,
    ReportLog,
    Anchor,
    ZKPNullifier,
    ReportStatus,
    ReportVisibility,
    RiskLevel,
    ModerationAction,
    ModerationDecision,
    LogEventType,
    Base,
)
from app.services.encryption_service import encryption_service


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session"""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_report_data():
    """Sample report data for testing"""
    return {
        "commitment_hash": "0x" + "a" * 64,
        "transaction_hash": "0x" + "b" * 64,
        "block_number": 12345678,
        "chain_id": 80001,  # Polygon Mumbai
        "ipfs_cid": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
        "ipfs_gateway_url": "https://nftstorage.link/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
        "file_size": 2457600,
        "file_type": "application/pdf",
        "visibility": ReportVisibility.MODERATED,
        "status": ReportStatus.PENDING,
        "verification_score": Decimal("0.85"),
        "risk_level": RiskLevel.MEDIUM,
    }


class TestReportModel:
    """Tests for Report model"""

    @pytest.mark.asyncio
    async def test_create_report(self, db_session, sample_report_data):
        """Test creating a new report"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        assert report.id is not None
        assert report.commitment_hash == sample_report_data["commitment_hash"]
        assert report.status == ReportStatus.PENDING
        assert report.created_at is not None

    @pytest.mark.asyncio
    async def test_report_unique_constraints(self, db_session, sample_report_data):
        """Test unique constraints on reports"""
        report1 = Report(**sample_report_data)
        db_session.add(report1)
        await db_session.commit()

        # Same commitment_hash should fail
        report2 = Report(**sample_report_data)
        report2.ipfs_cid = "QmDifferentCID"
        db_session.add(report2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_report_status_update(self, db_session, sample_report_data):
        """Test updating report status"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        original_updated_at = report.updated_at

        # Update status
        report.status = ReportStatus.UNDER_REVIEW
        await db_session.commit()
        await db_session.refresh(report)

        assert report.status == ReportStatus.UNDER_REVIEW
        # Note: updated_at trigger only works in PostgreSQL

    @pytest.mark.asyncio
    async def test_report_to_dict(self, db_session, sample_report_data):
        """Test report serialization to dict"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        report_dict = report.to_dict()

        assert "id" in report_dict
        assert report_dict["commitment_hash"] == sample_report_data["commitment_hash"]
        assert report_dict["status"] == "pending"
        assert report_dict["visibility"] == "moderated"

    @pytest.mark.asyncio
    async def test_report_soft_delete(self, db_session, sample_report_data):
        """Test soft delete functionality"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        # Soft delete
        report.deleted_at = datetime.utcnow()
        report.deletion_reason = "Test deletion"
        await db_session.commit()
        await db_session.refresh(report)

        assert report.deleted_at is not None
        assert report.deletion_reason == "Test deletion"

    @pytest.mark.asyncio
    async def test_report_dead_mans_switch(self, db_session, sample_report_data):
        """Test dead man's switch fields"""
        sample_report_data["dms_enabled"] = True
        sample_report_data["dms_trigger_date"] = datetime.utcnow() + timedelta(days=30)

        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        assert report.dms_enabled is True
        assert report.dms_released is False
        assert report.dms_trigger_date is not None


class TestModerationModel:
    """Tests for Moderation model"""

    @pytest.mark.asyncio
    async def test_create_moderation(self, db_session, sample_report_data):
        """Test creating a moderation action"""
        # Create report first
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        # Create moderation
        moderation = Moderation(
            report_id=report.id,
            moderator_id=uuid.uuid4(),
            action=ModerationAction.REVIEW_STARTED,
            ai_recommendation="accept",
            ai_confidence=Decimal("0.85"),
            ai_flags=["high_priority"],
        )
        db_session.add(moderation)
        await db_session.commit()
        await db_session.refresh(moderation)

        assert moderation.id is not None
        assert moderation.report_id == report.id
        assert moderation.action == ModerationAction.REVIEW_STARTED

    @pytest.mark.asyncio
    async def test_moderation_decision(self, db_session, sample_report_data):
        """Test moderation with decision"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        moderation = Moderation(
            report_id=report.id,
            action=ModerationAction.VERIFIED,
            decision=ModerationDecision.ACCEPT,
            verification_evidence="Cross-referenced with public records",
            time_spent_seconds=1200,
            completed_at=datetime.utcnow(),
        )
        db_session.add(moderation)
        await db_session.commit()
        await db_session.refresh(moderation)

        assert moderation.decision == ModerationDecision.ACCEPT
        assert moderation.completed_at is not None
        assert moderation.time_spent_seconds == 1200

    @pytest.mark.asyncio
    async def test_moderation_encrypted_notes(self, db_session, sample_report_data):
        """Test storing encrypted moderator notes"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        # Encrypt notes
        key = encryption_service.generate_key()
        notes = "This report requires additional verification."
        encrypted_notes = encryption_service.encrypt_string(notes, key)
        key_hash = encryption_service.hash_key(key)

        moderation = Moderation(
            report_id=report.id,
            action=ModerationAction.REQUEST_INFO,
            encrypted_notes=encrypted_notes,
            notes_encryption_key_hash=key_hash,
        )
        db_session.add(moderation)
        await db_session.commit()

        # Verify we can decrypt
        decrypted = encryption_service.decrypt_string(moderation.encrypted_notes, key)
        assert decrypted == notes

    @pytest.mark.asyncio
    async def test_moderation_to_dict(self, db_session, sample_report_data):
        """Test moderation serialization"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        moderation = Moderation(
            report_id=report.id,
            action=ModerationAction.REVIEW_STARTED,
            ai_confidence=Decimal("0.75"),
        )
        db_session.add(moderation)
        await db_session.commit()
        await db_session.refresh(moderation)

        mod_dict = moderation.to_dict()

        assert "id" in mod_dict
        assert mod_dict["action"] == "review_started"
        assert mod_dict["ai_confidence"] == 0.75


class TestReportLogModel:
    """Tests for ReportLog model"""

    @pytest.mark.asyncio
    async def test_create_log_entry(self, db_session, sample_report_data):
        """Test creating audit log entry"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        log = ReportLog(
            report_id=report.id,
            event_type=LogEventType.CREATED,
            event_data={"source": "web_form"},
        )
        db_session.add(log)
        await db_session.commit()
        await db_session.refresh(log)

        assert log.id is not None
        assert log.event_type == LogEventType.CREATED
        assert log.event_data["source"] == "web_form"

    @pytest.mark.asyncio
    async def test_log_status_change(self, db_session, sample_report_data):
        """Test logging status changes"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        log = ReportLog(
            report_id=report.id,
            actor_id=uuid.uuid4(),
            event_type=LogEventType.STATUS_CHANGED,
            field_changed="status",
            old_value="pending",
            new_value="under_review",
        )
        db_session.add(log)
        await db_session.commit()

        assert log.old_value == "pending"
        assert log.new_value == "under_review"

    @pytest.mark.asyncio
    async def test_multiple_log_entries(self, db_session, sample_report_data):
        """Test multiple log entries for a report"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        # Add multiple log entries
        for event_type in [LogEventType.CREATED, LogEventType.ACCESSED, LogEventType.STATUS_CHANGED]:
            log = ReportLog(
                report_id=report.id,
                event_type=event_type,
            )
            db_session.add(log)

        await db_session.commit()

        # Query logs
        result = await db_session.execute(
            select(ReportLog).where(ReportLog.report_id == report.id)
        )
        logs = result.scalars().all()

        assert len(logs) == 3


class TestZKPNullifierModel:
    """Tests for ZKP Nullifier model"""

    @pytest.mark.asyncio
    async def test_create_nullifier(self, db_session):
        """Test creating a ZKP nullifier"""
        nullifier = ZKPNullifier(
            nullifier="0x" + "1" * 64,
            commitment="0x" + "2" * 64,
        )
        db_session.add(nullifier)
        await db_session.commit()
        await db_session.refresh(nullifier)

        assert nullifier.id is not None
        assert nullifier.usage_count == 1
        assert nullifier.daily_report_count == 1

    @pytest.mark.asyncio
    async def test_nullifier_unique(self, db_session):
        """Test nullifier uniqueness"""
        nullifier_hash = "0x" + "a" * 64

        n1 = ZKPNullifier(
            nullifier=nullifier_hash,
            commitment="0x" + "b" * 64,
        )
        db_session.add(n1)
        await db_session.commit()

        n2 = ZKPNullifier(
            nullifier=nullifier_hash,
            commitment="0x" + "c" * 64,
        )
        db_session.add(n2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_nullifier_rate_limiting(self, db_session):
        """Test nullifier rate limiting fields"""
        nullifier = ZKPNullifier(
            nullifier="0x" + "d" * 64,
            commitment="0x" + "e" * 64,
            daily_report_count=5,
        )
        db_session.add(nullifier)
        await db_session.commit()
        await db_session.refresh(nullifier)

        # Increment count
        nullifier.usage_count += 1
        nullifier.daily_report_count += 1
        await db_session.commit()

        assert nullifier.usage_count == 2
        assert nullifier.daily_report_count == 6


class TestAnchorModel:
    """Tests for Anchor model"""

    @pytest.mark.asyncio
    async def test_create_anchor(self, db_session):
        """Test creating a daily anchor"""
        anchor = Anchor(
            merkle_root="0x" + "f" * 64,
            transaction_hash="0x" + "a" * 64,
            block_number=12345678,
            chain_id=80001,
            anchor_date=datetime.utcnow(),
            report_count=42,
            leaf_hashes=["hash1", "hash2", "hash3"],
        )
        db_session.add(anchor)
        await db_session.commit()
        await db_session.refresh(anchor)

        assert anchor.id is not None
        assert anchor.report_count == 42
        assert len(anchor.leaf_hashes) == 3


class TestReportRelationships:
    """Tests for model relationships"""

    @pytest.mark.asyncio
    async def test_report_moderations_relationship(self, db_session, sample_report_data):
        """Test report to moderations relationship"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        # Add multiple moderations
        for _ in range(3):
            moderation = Moderation(
                report_id=report.id,
                action=ModerationAction.REVIEW_STARTED,
            )
            db_session.add(moderation)

        await db_session.commit()
        await db_session.refresh(report)

        assert len(report.moderations) == 3

    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session, sample_report_data):
        """Test cascade delete removes related records"""
        report = Report(**sample_report_data)
        db_session.add(report)
        await db_session.commit()

        # Add moderation and log
        moderation = Moderation(
            report_id=report.id,
            action=ModerationAction.VERIFIED,
        )
        log = ReportLog(
            report_id=report.id,
            event_type=LogEventType.CREATED,
        )
        db_session.add_all([moderation, log])
        await db_session.commit()

        moderation_id = moderation.id
        log_id = log.id

        # Delete report
        await db_session.delete(report)
        await db_session.commit()

        # Verify related records are deleted
        mod_result = await db_session.execute(
            select(Moderation).where(Moderation.id == moderation_id)
        )
        assert mod_result.scalars().first() is None

        log_result = await db_session.execute(
            select(ReportLog).where(ReportLog.id == log_id)
        )
        assert log_result.scalars().first() is None


class TestEncryptionServiceIntegration:
    """Tests for encryption service with database models"""

    def test_generate_commitment_hash(self):
        """Test generating commitment hash"""
        cid = "QmTestCID123"
        hash_result = encryption_service.compute_commitment_hash(cid)

        assert hash_result.startswith("0x")
        assert len(hash_result) == 66

    def test_generate_nullifier(self):
        """Test generating nullifier"""
        nullifier = encryption_service.generate_nullifier()

        assert nullifier.startswith("0x")
        assert len(nullifier) == 66

    def test_encrypt_decrypt_moderator_notes(self):
        """Test encrypting and decrypting moderator notes"""
        key = encryption_service.generate_key()
        notes = "Sensitive moderator notes"

        encrypted = encryption_service.encrypt_string(notes, key)
        decrypted = encryption_service.decrypt_string(encrypted, key)

        assert decrypted == notes
        assert encrypted != notes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
