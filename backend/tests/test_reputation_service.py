import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from app.services.reputation_service import ReputationService, reputation_service
from app.models.moderator import Moderator


class TestReputationService:
    @pytest.fixture
    def service(self):
        return ReputationService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_moderator(self):
        moderator = Mock(spec=Moderator)
        moderator.id = "test-id"
        moderator.wallet_address = "0x1234567890123456789012345678901234567890"
        moderator.reputation_score = 100
        moderator.tier = "silver"
        moderator.total_reviews = 10
        moderator.accurate_reviews = 8
        moderator.disputed_reviews = 1
        moderator.is_active = True
        moderator.is_suspended = False
        moderator.can_moderate = Mock(return_value=True)
        moderator.last_active_at = datetime.utcnow()
        moderator.updated_at = datetime.utcnow()
        return moderator

    def test_calculate_tier_bronze(self, service):
        assert service._calculate_tier(0) == 'bronze'
        assert service._calculate_tier(50) == 'bronze'
        assert service._calculate_tier(99) == 'bronze'

    def test_calculate_tier_silver(self, service):
        assert service._calculate_tier(100) == 'silver'
        assert service._calculate_tier(250) == 'silver'
        assert service._calculate_tier(499) == 'silver'

    def test_calculate_tier_gold(self, service):
        assert service._calculate_tier(500) == 'gold'
        assert service._calculate_tier(750) == 'gold'
        assert service._calculate_tier(999) == 'gold'

    def test_calculate_tier_platinum(self, service):
        assert service._calculate_tier(1000) == 'platinum'
        assert service._calculate_tier(5000) == 'platinum'

    @pytest.mark.asyncio
    async def test_update_reputation_accurate_review(self, service, mock_db, mock_moderator):
        mock_db.get.return_value = mock_moderator

        result = await service.update_reputation_after_moderation(
            mock_db, "test-id", was_accurate=True, was_disputed=False
        )

        assert result.total_reviews == 11
        assert result.accurate_reviews == 9
        assert result.reputation_score == 110

    @pytest.mark.asyncio
    async def test_update_reputation_disputed_review(self, service, mock_db, mock_moderator):
        mock_db.get.return_value = mock_moderator

        result = await service.update_reputation_after_moderation(
            mock_db, "test-id", was_accurate=False, was_disputed=True
        )

        assert result.total_reviews == 11
        assert result.disputed_reviews == 2
        assert result.reputation_score == 80

    @pytest.mark.asyncio
    async def test_update_reputation_tier_upgrade(self, service, mock_db, mock_moderator):
        mock_moderator.reputation_score = 495

        mock_db.get.return_value = mock_moderator

        result = await service.update_reputation_after_moderation(
            mock_db, "test-id", was_accurate=True, was_disputed=False
        )

        assert result.tier == 'gold'

    @pytest.mark.asyncio
    async def test_update_reputation_moderator_not_found(self, service, mock_db):
        mock_db.get.return_value = None

        with pytest.raises(ValueError, match="Moderator .* not found"):
            await service.update_reputation_after_moderation(
                mock_db, "nonexistent", True, False
            )

    @pytest.mark.asyncio
    async def test_update_reputation_inactive_moderator(self, service, mock_db, mock_moderator):
        mock_moderator.is_active = False
        mock_db.get.return_value = mock_moderator

        with pytest.raises(ValueError, match="Moderator .* is not active"):
            await service.update_reputation_after_moderation(
                mock_db, "test-id", True, False
            )

    @pytest.mark.asyncio
    async def test_apply_decay_no_decay_needed(self, service, mock_moderator):
        mock_moderator.updated_at = datetime.utcnow() - timedelta(days=3)

        result = await service._apply_decay_if_needed(None, mock_moderator)

        assert result is False
        assert mock_moderator.reputation_score == 100

    @pytest.mark.asyncio
    async def test_apply_decay_single_period(self, service, mock_moderator):
        mock_moderator.updated_at = datetime.utcnow() - timedelta(days=8)

        result = await service._apply_decay_if_needed(None, mock_moderator)

        assert result is True
        assert mock_moderator.reputation_score == 99

    @pytest.mark.asyncio
    async def test_apply_decay_multiple_periods(self, service, mock_moderator):
        mock_moderator.updated_at = datetime.utcnow() - timedelta(days=22)

        result = await service._apply_decay_if_needed(None, mock_moderator)

        assert result is True
        assert mock_moderator.reputation_score == 97

    @pytest.mark.asyncio
    async def test_apply_decay_with_tier_change(self, service, mock_moderator):
        mock_moderator.reputation_score = 101
        mock_moderator.tier = 'silver'
        mock_moderator.updated_at = datetime.utcnow() - timedelta(days=15)

        result = await service._apply_decay_if_needed(None, mock_moderator)

        assert result is True
        assert mock_moderator.reputation_score == 99
        assert mock_moderator.tier == 'bronze'

    @pytest.mark.asyncio
    async def test_get_moderator_stats(self, service, mock_db, mock_moderator):
        mock_db.get.return_value = mock_moderator

        stats = await service.get_moderator_stats(mock_db, "test-id")

        assert stats['moderator_id'] == "test-id"
        assert stats['reputation_score'] == 100
        assert stats['tier'] == 'silver'
        assert stats['total_reviews'] == 10
        assert stats['accurate_reviews'] == 8
        assert stats['accuracy_rate'] == 80.0
        assert stats['daily_rate_limit'] == 10

    @pytest.mark.asyncio
    async def test_calculate_rate_limit(self, service, mock_db, mock_moderator):
        mock_db.get.return_value = mock_moderator

        rate_limit = await service.calculate_rate_limit(mock_db, "test-id")

        assert rate_limit == 10

    @pytest.mark.asyncio
    async def test_calculate_rate_limit_moderator_not_found(self, service, mock_db):
        mock_db.get.return_value = None

        rate_limit = await service.calculate_rate_limit(mock_db, "nonexistent")

        assert rate_limit == 5

    def test_tier_rate_limits(self, service):
        assert service.TIER_RATE_LIMITS['bronze'] == 5
        assert service.TIER_RATE_LIMITS['silver'] == 10
        assert service.TIER_RATE_LIMITS['gold'] == 20
        assert service.TIER_RATE_LIMITS['platinum'] == 50

    def test_scoring_constants(self, service):
        assert service.ACCURATE_REVIEW_POINTS == 10
        assert service.DISPUTED_REVIEW_PENALTY == 20
        assert service.DECAY_RATE == 1
        assert service.DECAY_INTERVAL_DAYS == 7

    def test_tier_thresholds(self, service):
        assert service.BRONZE_THRESHOLD == 0
        assert service.SILVER_THRESHOLD == 100
        assert service.GOLD_THRESHOLD == 500
        assert service.PLATINUM_THRESHOLD == 1000
