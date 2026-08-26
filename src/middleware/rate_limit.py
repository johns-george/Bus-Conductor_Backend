"""Simple in-memory sliding-window rate limiter.

For multi-instance deployments, replace with Redis-backed limiter
(e.g., slowapi or custom Redis implementation).
"""

import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = None, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/", "/health", "/test-db"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self.window

        # Clean old entries
        self._hits[client_ip] = [
            t for t in self._hits[client_ip] if t > cutoff
        ]

        if len(self._hits[client_ip]) >= self.max_requests:
            retry_after = int(self._hits[client_ip][0] + self.window - now) + 1
            return Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._hits[client_ip].append(now)
        response = await call_next(request)
        remaining = self.max_requests - len(self._hits[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
