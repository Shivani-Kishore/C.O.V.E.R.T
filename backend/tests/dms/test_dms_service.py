"""
Tests for DMS Service
"""

import pytest
from datetime import datetime, timedelta
from app.services.dms.dms_service import DMSService
from app.models.dms import DeadMansSwitch, DMSCheckIn, DMSStatus


class TestDMSService:
    @pytest.fixture
    def service(self):
        return DMSService()

    @pytest.fixture
    def future_date(self):
        return datetime.utcnow() + timedelta(days=30)

    @pytest.fixture
    async def mock_report(self, db_session):
        """Mock report for testing"""
        # In real test, would create actual report
        return {
            'id': 'test-report-id',
            'reporter_nullifier': '0x' + '1' * 64
        }

    @pytest.mark.asyncio
    async def test_create_dms(self, service, db_session, mock_report, future_date):
        """Test DMS creation"""
        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date,
            trigger_type='time_based'
        )

        assert dms is not None
        assert dms.report_id == mock_report['id']
        assert dms.status == DMSStatus.ACTIVE
        assert dms.trigger_date == future_date

    @pytest.mark.asyncio
    async def test_create_dms_duplicate(self, service, db_session, mock_report, future_date):
        """Test that duplicate DMS cannot be created"""
        # Create first DMS
        dms1 = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Attempt to create duplicate
        dms2 = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        assert dms1 is not None
        assert dms2 is None

    @pytest.mark.asyncio
    async def test_check_in(self, service, db_session, mock_report, future_date):
        """Test DMS check-in"""
        # Create DMS
        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Check in
        check_in = await service.check_in(
            db_session,
            dms_id=str(dms.id),
            reporter_nullifier=mock_report['reporter_nullifier'],
            proof_of_life="Still here"
        )

        assert check_in is not None
        assert check_in.proof_of_life == "Still here"

        # Verify DMS updated
        await db_session.refresh(dms)
        assert dms.check_in_count == 1
        assert dms.last_check_in is not None

    @pytest.mark.asyncio
    async def test_check_in_with_extension(self, service, db_session, mock_report, future_date):
        """Test check-in with trigger date extension"""
        # Create DMS
        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        original_date = dms.trigger_date
        new_date = future_date + timedelta(days=30)

        # Check in with extension
        check_in = await service.check_in(
            db_session,
            dms_id=str(dms.id),
            reporter_nullifier=mock_report['reporter_nullifier'],
            extend_trigger_date=new_date,
            extension_reason="Need more time"
        )

        assert check_in is not None

        # Verify trigger date extended
        await db_session.refresh(dms)
        assert dms.trigger_date == new_date
        assert dms.trigger_date > original_date
        assert dms.status == DMSStatus.EXTENDED

    @pytest.mark.asyncio
    async def test_cancel_dms(self, service, db_session, mock_report, future_date):
        """Test DMS cancellation"""
        # Create DMS
        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Cancel DMS
        success = await service.cancel_dms(
            db_session,
            dms_id=str(dms.id),
            reporter_nullifier=mock_report['reporter_nullifier'],
            reason="No longer needed"
        )

        assert success is True

        # Verify status
        await db_session.refresh(dms)
        assert dms.status == DMSStatus.CANCELLED
        assert dms.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_cancel_unauthorized(self, service, db_session, mock_report, future_date):
        """Test that unauthorized user cannot cancel DMS"""
        # Create DMS
        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Attempt to cancel with wrong nullifier
        success = await service.cancel_dms(
            db_session,
            dms_id=str(dms.id),
            reporter_nullifier='0x' + '2' * 64,
            reason="Unauthorized attempt"
        )

        assert success is False

        # Verify still active
        await db_session.refresh(dms)
        assert dms.status == DMSStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_pending_triggers(self, service, db_session, mock_report):
        """Test getting pending triggers"""
        # Create DMS with past trigger date
        past_date = datetime.utcnow() - timedelta(days=1)

        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=past_date
        )

        # Get pending triggers
        pending = await service.get_pending_triggers(db_session)

        assert len(pending) >= 1
        assert any(str(d.id) == str(dms.id) for d in pending)

    @pytest.mark.asyncio
    async def test_get_dms_by_report(self, service, db_session, mock_report, future_date):
        """Test getting DMS by report ID"""
        # Create DMS
        dms = await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Get by report
        found_dms = await service.get_dms_by_report(db_session, mock_report['id'])

        assert found_dms is not None
        assert str(found_dms.id) == str(dms.id)

    @pytest.mark.asyncio
    async def test_get_dms_by_nullifier(self, service, db_session, mock_report, future_date):
        """Test getting all DMS for a reporter"""
        # Create multiple DMS for same reporter
        dms1 = await service.create_dms(
            db_session,
            report_id=mock_report['id'] + '_1',
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        dms2 = await service.create_dms(
            db_session,
            report_id=mock_report['id'] + '_2',
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Get by nullifier
        all_dms = await service.get_dms_by_nullifier(
            db_session,
            mock_report['reporter_nullifier']
        )

        assert len(all_dms) >= 2
        dms_ids = [str(d.id) for d in all_dms]
        assert str(dms1.id) in dms_ids
        assert str(dms2.id) in dms_ids

    @pytest.mark.asyncio
    async def test_get_statistics(self, service, db_session, mock_report, future_date):
        """Test getting DMS statistics"""
        # Create some DMS
        await service.create_dms(
            db_session,
            report_id=mock_report['id'],
            reporter_nullifier=mock_report['reporter_nullifier'],
            trigger_date=future_date
        )

        # Get statistics
        stats = await service.get_dms_statistics(db_session)

        assert 'total_active' in stats
        assert 'total_released' in stats
        assert 'pending_triggers_24h' in stats
        assert stats['total_active'] >= 1
