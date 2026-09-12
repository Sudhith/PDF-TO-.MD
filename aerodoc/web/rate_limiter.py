"""
Sliding-Window Rate Limiter
In-memory, thread-safe rate limiter tracking per-client request velocity
with automatic timestamp eviction and Retry-After calculation.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from aerodoc.exceptions import RateLimitExceededError


class SlidingWindowRateLimiter:
    """Sliding-window velocity limiter keyed by client IP."""

    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Tests whether client_id can make a request.
        Returns: (is_allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Purge timestamps outside current window
            timestamps = [t for t in self._requests[client_id] if t > window_start]
            self._requests[client_id] = timestamps

            if len(timestamps) >= self.max_requests:
                # Calculate remaining seconds until oldest request in window expires
                oldest_in_window = timestamps[0]
                retry_after = max(1, int(oldest_in_window + self.window_seconds - now))
                return False, retry_after

            # Record current request timestamp
            self._requests[client_id].append(now)
            return True, 0

    def reset(self):
        """Clears all stored rate limit history."""
        with self._lock:
            self._requests.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware enforcing rate limits on conversion endpoints."""

    def __init__(self, app, conversion_limit: int = 15, general_limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.conversion_limiter = SlidingWindowRateLimiter(max_requests=conversion_limit, window_seconds=window_seconds)
        self.general_limiter = SlidingWindowRateLimiter(max_requests=general_limit, window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next):
        # Extract client IP
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")

        path = request.url.path

        # Check conversion endpoint specifically
        if path.startswith("/api/convert"):
            allowed, retry_after = self.conversion_limiter.is_allowed(client_ip)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Conversion rate limit exceeded. Please wait {retry_after}s before converting again.",
                            "details": {"retry_after_seconds": retry_after}
                        }
                    },
                    headers={"Retry-After": str(retry_after)}
                )
        elif path.startswith("/api/"):
            allowed, retry_after = self.general_limiter.is_allowed(client_ip)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Too many requests. Please wait {retry_after}s.",
                            "details": {"retry_after_seconds": retry_after}
                        }
                    },
                    headers={"Retry-After": str(retry_after)}
                )

        return await call_next(request)
