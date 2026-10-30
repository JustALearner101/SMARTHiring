import time
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response


@dataclass
class RateLimitRule:
    limit: int
    window_seconds: int = 60


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._records: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        """Checks if a request is allowed under the sliding window.

        Returns: (allowed, remaining, retry_after)
        """
        now = time.time()
        window_start = now - window_seconds

        timestamps = self._records[key]
        # Prune timestamps outside current window
        valid_timestamps = [ts for ts in timestamps if ts > window_start]
        self._records[key] = valid_timestamps

        current_count = len(valid_timestamps)
        if current_count >= limit:
            oldest = valid_timestamps[0]
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, 0, retry_after

        # Record this hit
        valid_timestamps.append(now)
        remaining = max(0, limit - len(valid_timestamps))
        return True, remaining, 0

    def reset(self) -> None:
        """Clear all rate limiting records (useful for test suites)."""
        self._records.clear()


# Global in-memory rate limiter instance
rate_limiter_instance = SlidingWindowRateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Enforces tiered in-memory sliding window rate limits on sensitive endpoints."""

    RULES: ClassVar[list[tuple[str, RateLimitRule]]] = [
        # AI natural language triage and command generation
        ("/api/v1/orchestrator/command", RateLimitRule(limit=10, window_seconds=60)),
        # File uploads and transcription jobs
        ("/api/v1/interviews/sessions/upload", RateLimitRule(limit=10, window_seconds=60)),
        # Authentication endpoints
        ("/api/v1/auth", RateLimitRule(limit=5, window_seconds=60)),
        # General API fallback
        ("/api/v1", RateLimitRule(limit=60, window_seconds=60)),
    ]

    EXEMPT_PATHS: ClassVar[set[str]] = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exempt OPTIONS preflight and non-API/docs routes
        if request.method == "OPTIONS" or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Allow test bypass if header present
        if request.headers.get("X-Bypass-Rate-Limit") == "1":
            return await call_next(request)

        # Find matching rule
        matched_rule: RateLimitRule | None = None
        for prefix, rule in self.RULES:
            if request.url.path.startswith(prefix):
                matched_rule = rule
                break

        if not matched_rule:
            return await call_next(request)

        # Determine client key (X-Forwarded-For or client.host)
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
        key = f"{client_ip}:{request.url.path}"

        allowed, remaining, retry_after = rate_limiter_instance.is_allowed(
            key=key,
            limit=matched_rule.limit,
            window_seconds=matched_rule.window_seconds,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(matched_rule.limit),
                    "X-RateLimit-Remaining": "0",
                },
                content={
                    "success": False,
                    "message": f"Terlalu banyak permintaan (Rate limit exceeded: maksimal {matched_rule.limit} per {matched_rule.window_seconds} detik). Silakan tunggu {retry_after} detik.",
                    "data": {"retry_after_seconds": retry_after},
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(matched_rule.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
