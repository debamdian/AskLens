"""Sliding-Window Rate Limiter Middleware for FastAPI."""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter keyed by client identifier."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """Check if request is allowed; returns (allowed, remaining_quota)."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        dq = self._requests[key]

        while dq and dq[0] < cutoff:
            dq.popleft()

        if len(dq) >= self.max_requests:
            return False, 0

        dq.append(now)
        return True, self.max_requests - len(dq)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing per-IP sliding window rate limits on /api/ routes."""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining = self.limiter.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please wait before sending more requests."},
                headers={"Retry-After": str(self.limiter.window_seconds)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
