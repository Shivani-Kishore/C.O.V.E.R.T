import pytest
import time
from app.security.rate_limiter import (
    RateLimiter,
    TieredRateLimiter,
    BurstRateLimiter,
    RateLimitExceeded
)


class TestRateLimiter:
    @pytest.fixture
    def limiter(self):
        return RateLimiter()

    def test_allow_within_limit(self, limiter):
        identifier = "test_user"

        for i in range(5):
            result = limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)
            assert result is True

    def test_block_over_limit(self, limiter):
        identifier = "test_user_2"

        for i in range(5):
            limiter.check_rate_limit(identifier, max_requests=5, window_seconds=60)

        with pytest.raises(RateLimitExceeded):
            limiter.check_rate_limit(identifier, max_requests=5, window_seconds=60)

    def test_window_expiry(self, limiter):
        identifier = "test_user_3"

        limiter.check_rate_limit(identifier, max_requests=2, window_seconds=1)

        with pytest.raises(RateLimitExceeded):
            limiter.check_rate_limit(identifier, max_requests=2, window_seconds=1)

        time.sleep(1.5)

        result = limiter.check_rate_limit(identifier, max_requests=2, window_seconds=1)
        assert result is True

    def test_different_endpoints(self, limiter):
        identifier = "test_user_4"

        limiter.check_rate_limit(identifier, max_requests=2, window_seconds=60, endpoint="/api/v1/reports")
        limiter.check_rate_limit(identifier, max_requests=2, window_seconds=60, endpoint="/api/v1/reports")

        limiter.check_rate_limit(identifier, max_requests=2, window_seconds=60, endpoint="/api/v1/users")
        limiter.check_rate_limit(identifier, max_requests=2, window_seconds=60, endpoint="/api/v1/users")

    def test_cleanup_old_entries(self, limiter):
        identifier = "test_user_5"

        limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)

        initial_size = len(limiter.requests)

        limiter.last_cleanup = time.time() - 4000
        limiter._cleanup_old_entries()


class TestTieredRateLimiter:
    @pytest.fixture
    def tiered_limiter(self):
        return TieredRateLimiter()

    def test_anonymous_tier(self, tiered_limiter):
        identifier = "anonymous_user"

        for i in range(10):
            result = tiered_limiter.check_tiered_limit(identifier, tier='anonymous')
            assert result is True

        with pytest.raises(RateLimitExceeded):
            tiered_limiter.check_tiered_limit(identifier, tier='anonymous')

    def test_bronze_tier(self, tiered_limiter):
        identifier = "bronze_user"

        for i in range(20):
            result = tiered_limiter.check_tiered_limit(identifier, tier='bronze')
            assert result is True

        with pytest.raises(RateLimitExceeded):
            tiered_limiter.check_tiered_limit(identifier, tier='bronze')

    def test_silver_tier(self, tiered_limiter):
        identifier = "silver_user"

        for i in range(50):
            result = tiered_limiter.check_tiered_limit(identifier, tier='silver')
            assert result is True

    def test_gold_tier(self, tiered_limiter):
        identifier = "gold_user"

        for i in range(100):
            result = tiered_limiter.check_tiered_limit(identifier, tier='gold')
            assert result is True

    def test_platinum_tier(self, tiered_limiter):
        identifier = "platinum_user"

        for i in range(200):
            result = tiered_limiter.check_tiered_limit(identifier, tier='platinum')
            assert result is True

    def test_invalid_tier_defaults_to_anonymous(self, tiered_limiter):
        identifier = "invalid_tier_user"

        for i in range(10):
            tiered_limiter.check_tiered_limit(identifier, tier='invalid')

        with pytest.raises(RateLimitExceeded):
            tiered_limiter.check_tiered_limit(identifier, tier='invalid')


class TestBurstRateLimiter:
    @pytest.fixture
    def burst_limiter(self):
        return BurstRateLimiter()

    def test_allow_within_burst(self, burst_limiter):
        identifier = "burst_user"

        for i in range(5):
            result = burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=10)
            assert result is True

        with pytest.raises(RateLimitExceeded):
            burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=10)

    def test_burst_window_expiry(self, burst_limiter):
        identifier = "burst_user_2"

        for i in range(5):
            burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=1)

        with pytest.raises(RateLimitExceeded):
            burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=1)

        time.sleep(1.5)

        result = burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=1)
        assert result is True

    def test_burst_protects_against_rapid_requests(self, burst_limiter):
        identifier = "rapid_user"

        for i in range(5):
            burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=10)

        with pytest.raises(RateLimitExceeded):
            burst_limiter.check_burst_limit(identifier, max_burst=5, burst_window=10)
