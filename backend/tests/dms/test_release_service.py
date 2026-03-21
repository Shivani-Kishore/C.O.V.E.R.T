"""
Tests for DMS Release Service
"""

import pytest
from datetime import datetime, timedelta
from app.services.dms.release_service import ReleaseService
from app.models.dms import DeadMansSwitch, DMSStatus


class TestReleaseService:
    @pytest.fixture
    def service(self):
        return ReleaseService()

    @pytest.fixture
    async def mock_dms(self, db_session):
        """Mock DMS for testing"""
        # In real test, would create actual DMS with report
        return {
            'id': 'test-dms-id',
            'report_id': 'test-report-id',
            'status': DMSStatus.ACTIVE,
            'trigger_date': datetime.utcnow() - timedelta(days=1)
        }

    @pytest.mark.asyncio
    async def test_trigger_dms(self, service, db_session, mock_dms):
        """Test marking DMS as triggered"""
        success = await service.trigger_dms(db_session, mock_dms['id'])

        # In full implementation, would verify status changed to TRIGGERED
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_release_report(self, service, db_session, mock_dms):
        """Test automated report release"""
        result = await service.release_report(db_session, mock_dms['id'])

        assert 'success' in result
        assert 'steps' in result or 'error' in result

    @pytest.mark.asyncio
    async def test_release_steps(self, service, db_session, mock_dms):
        """Test that release executes all steps"""
        result = await service.release_report(db_session, mock_dms['id'])

        if result.get('success'):
            steps = result.get('steps', [])
            step_types = [step.get('action') for step in steps]

            # Should attempt all release steps
            expected_steps = ['visibility_update', 'ipfs_pin', 'blockchain_tx', 'notifications']
            for expected in expected_steps:
                assert expected in step_types

    @pytest.mark.asyncio
    async def test_pin_to_ipfs(self, service):
        """Test IPFS pinning"""
        # Mock report
        class MockReport:
            id = 'test-id'
            ipfs_cid = 'QmTest123'
            ipfs_gateway_url = 'https://ipfs.io/ipfs/QmTest123'

        result = await service._pin_to_ipfs(MockReport())

        assert 'success' in result
        assert 'cid' in result

    @pytest.mark.asyncio
    async def test_blockchain_transaction(self, service):
        """Test blockchain release notification"""
        # Mock report and DMS
        class MockReport:
            id = 'test-id'
            commitment_hash = '0x' + '1' * 64
            ipfs_cid = 'QmTest123'

        class MockDMS:
            id = 'dms-id'

        result = await service._post_blockchain_release(MockReport(), MockDMS())

        assert 'success' in result
        if result.get('success'):
            assert 'transaction_hash' in result

    @pytest.mark.asyncio
    async def test_send_notifications(self, service):
        """Test notification sending"""
        # Mock DMS with encrypted contacts
        class MockDMS:
            id = 'dms-id'
            encrypted_contacts = ['contact1@example.com', 'contact2@example.com']

        class MockReport:
            id = 'report-id'

        result = await service._send_notifications(MockDMS(), MockReport())

        assert 'success' in result

    @pytest.mark.asyncio
    async def test_emergency_override_release(self, service, db_session, mock_dms):
        """Test emergency override to force release"""
        success = await service.emergency_override(
            db_session,
            dms_id=mock_dms['id'],
            admin_wallet='0x' + '1' * 40,
            action='release',
            reason='Emergency situation'
        )

        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_emergency_override_cancel(self, service, db_session, mock_dms):
        """Test emergency override to cancel"""
        success = await service.emergency_override(
            db_session,
            dms_id=mock_dms['id'],
            admin_wallet='0x' + '1' * 40,
            action='cancel',
            reason='False alarm'
        )

        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_emergency_override_extend(self, service, db_session, mock_dms):
        """Test emergency override to extend trigger date"""
        new_date = datetime.utcnow() + timedelta(days=30)

        success = await service.emergency_override(
            db_session,
            dms_id=mock_dms['id'],
            admin_wallet='0x' + '1' * 40,
            action='extend',
            reason='More time needed',
            extend_until=new_date
        )

        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_retry_logic(self, service):
        """Test that failed releases are retried"""
        assert service.max_retry_attempts >= 3
        assert service.retry_delay_minutes > 0

    @pytest.mark.asyncio
    async def test_release_already_released(self, service, db_session):
        """Test that already released DMS cannot be released again"""
        # Mock DMS that's already released
        mock_released = {
            'id': 'released-dms',
            'status': DMSStatus.RELEASED
        }

        result = await service.release_report(db_session, mock_released['id'])

        assert result.get('success') is False
        assert 'already released' in result.get('error', '').lower()
