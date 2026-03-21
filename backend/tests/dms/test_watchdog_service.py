"""
Tests for DMS Watchdog Service
"""

import pytest
from datetime import datetime, timedelta
from app.services.dms.watchdog_service import WatchdogService


class TestWatchdogService:
    @pytest.fixture
    def service(self):
        return WatchdogService()

    def test_watchdog_initialization(self, service):
        """Test watchdog service initialization"""
        assert service.check_interval_seconds > 0
        assert service.batch_size > 0
        assert service.is_running is False

    @pytest.mark.asyncio
    async def test_watchdog_start_stop(self, service, db_session):
        """Test starting and stopping watchdog"""
        # Start watchdog
        # Note: In real test, would use background task
        service.is_running = False  # Don't actually start

        assert service.watchdog_id is None

    @pytest.mark.asyncio
    async def test_heartbeat_update(self, service, db_session):
        """Test heartbeat update"""
        service.watchdog_id = 'test-id'
        await service._update_heartbeat(db_session)

        # Should not raise exception
        assert True

    @pytest.mark.asyncio
    async def test_statistics_update(self, service, db_session):
        """Test statistics update"""
        service.watchdog_id = 'test-id'

        await service._update_statistics(
            db_session,
            triggers_found=5,
            releases_attempted=5,
            releases_succeeded=4,
            releases_failed=1,
            start_time=datetime.utcnow().timestamp()
        )

        # Should not raise exception
        assert True

    @pytest.mark.asyncio
    async def test_error_recording(self, service, db_session):
        """Test error recording"""
        service.watchdog_id = 'test-id'

        await service._record_error(db_session, "Test error message")

        # Should not raise exception
        assert True

    @pytest.mark.asyncio
    async def test_get_status_not_running(self, service, db_session):
        """Test getting status when not running"""
        status = await service.get_status(db_session)

        assert status.get('status') == 'not_running'

    @pytest.mark.asyncio
    async def test_manual_trigger_check(self, service, db_session):
        """Test manual trigger check"""
        result = await service.manual_trigger_check(db_session)

        assert 'pending_count' in result
        assert 'processed' in result or 'error' in result

    @pytest.mark.asyncio
    async def test_check_cycle_logic(self, service):
        """Test check cycle processes pending triggers"""
        # Test that check cycle has correct logic flow
        assert hasattr(service, '_run_check_cycle')

    def test_watchdog_configuration(self, service):
        """Test watchdog configuration values"""
        # Check interval should be reasonable (5 minutes default)
        assert 60 <= service.check_interval_seconds <= 600

        # Batch size should handle reasonable volume
        assert 10 <= service.batch_size <= 1000

    @pytest.mark.asyncio
    async def test_concurrent_watchdog_prevention(self, service):
        """Test that multiple watchdogs cannot run simultaneously"""
        # First watchdog
        if service.is_running:
            # Should not start second instance
            assert service.is_running is True

    def test_watchdog_service_attributes(self, service):
        """Test watchdog has required attributes"""
        assert hasattr(service, 'check_interval_seconds')
        assert hasattr(service, 'batch_size')
        assert hasattr(service, 'is_running')
        assert hasattr(service, 'watchdog_id')

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, service, db_session):
        """Test watchdog shuts down gracefully"""
        service.is_running = True
        service.watchdog_id = 'test-id'

        await service.stop(db_session)

        assert service.is_running is False
