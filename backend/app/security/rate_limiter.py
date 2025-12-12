import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 3600
        self.last_cleanup = time.time()

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        endpoint: Optional[str] = None
    ) -> bool:
        self._cleanup_old_entries()

        key = f"{identifier}:{endpoint}" if endpoint else identifier
        now = time.time()
        window_start = now - window_seconds

        if key not in self.requests:
            self.requests[key] = []

        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        current_count = len(self.requests[key])

        if current_count >= max_requests:
            oldest_request = min(self.requests[key])
            retry_after = int(window_seconds - (now - oldest_request))
            logger.warning(
                f"Rate limit exceeded for {identifier}: "
                f"{current_count}/{max_requests} in {window_seconds}s"
            )
            raise RateLimitExceeded(retry_after)

        self.requests[key].append(now)
        return True

    def _cleanup_old_entries(self):
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = now - 86400
        keys_to_delete = []

        for key, timestamps in self.requests.items():
            self.requests[key] = [t for t in timestamps if t > cutoff_time]
            if not self.requests[key]:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.requests[key]

        self.last_cleanup = now
        logger.info(f"Cleaned up {len(keys_to_delete)} expired rate limit entries")

    def get_identifier(self, request: Request) -> str:
        if hasattr(request.state, 'user_id'):
            return f"user:{request.state.user_id}"

        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        user_agent = request.headers.get('User-Agent', '')
        identifier = f"{ip}:{user_agent}"

        return hashlib.sha256(identifier.encode()).hexdigest()[:16]


class TieredRateLimiter(RateLimiter):
    TIER_LIMITS = {
        'anonymous': {'max_requests': 10, 'window': 3600},
        'bronze': {'max_requests': 20, 'window': 3600},
        'silver': {'max_requests': 50, 'window': 3600},
        'gold': {'max_requests': 100, 'window': 3600},
        'platinum': {'max_requests': 200, 'window': 3600},
    }

    def check_tiered_limit(
        self,
        identifier: str,
        tier: str = 'anonymous',
        endpoint: Optional[str] = None
    ) -> bool:
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['anonymous'])

        return self.check_rate_limit(
            identifier,
            max_requests=limits['max_requests'],
            window_seconds=limits['window'],
            endpoint=endpoint
        )


class BurstRateLimiter(RateLimiter):
    def __init__(self):
        super().__init__()
        self.burst_requests: Dict[str, list] = defaultdict(list)

    def check_burst_limit(
        self,
        identifier: str,
        max_burst: int = 5,
        burst_window: int = 10
    ) -> bool:
        now = time.time()
        window_start = now - burst_window

        if identifier not in self.burst_requests:
            self.burst_requests[identifier] = []

        self.burst_requests[identifier] = [
            req_time for req_time in self.burst_requests[identifier]
            if req_time > window_start
        ]

        if len(self.burst_requests[identifier]) >= max_burst:
            retry_after = int(burst_window)
            logger.warning(f"Burst limit exceeded for {identifier}")
            raise RateLimitExceeded(retry_after)

        self.burst_requests[identifier].append(now)
        return True


rate_limiter = RateLimiter()
tiered_rate_limiter = TieredRateLimiter()
burst_rate_limiter = BurstRateLimiter()
