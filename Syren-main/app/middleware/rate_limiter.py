"""Token-bucket rate limiter middleware."""

from __future__ import annotations
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.config import get_settings


@dataclass
class _Bucket:
    tokens: float
    max_tokens: float
    refill_rate: float
    last_refill: float = field(default_factory=time.monotonic)

    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def retry_after(self) -> float:
        self._refill()
        return max(0, (1 - self.tokens) / self.refill_rate)

    def _refill(self) -> None:
        now = time.monotonic()
        self.tokens = min(self.max_tokens, self.tokens + (now - self.last_refill) * self.refill_rate)
        self.last_refill = now


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30, burst_size: int | None = None) -> None:
        self._max_tokens = burst_size or int(requests_per_minute * 1.5)
        self._refill_rate = requests_per_minute / 60.0
        self._lock = Lock()
        self._buckets: Dict[str, _Bucket] = {}

    def _get_bucket(self, key: str) -> _Bucket:
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = _Bucket(tokens=self._max_tokens, max_tokens=self._max_tokens,
                                              refill_rate=self._refill_rate)
            return self._buckets[key]

    def is_allowed(self, key: str) -> Tuple[bool, float]:
        bucket = self._get_bucket(key)
        if bucket.consume():
            return True, 0.0
        return False, bucket.retry_after()

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    WHITELISTED_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, limiter: RateLimiter | None = None) -> None:
        super().__init__(app)
        settings = get_settings()
        self._limiter = limiter or RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.WHITELISTED_PATHS:
            return await call_next(request)
        client_ip = self._extract_ip(request)
        allowed, retry_after = self._limiter.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error": "Too Many Requests", "detail": f"Retry after {retry_after:.1f}s.",
                         "retry_after": round(retry_after, 1)},
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Policy"] = f"{int(self._limiter._refill_rate * 60)};w=60"
        return response

    @staticmethod
    def _extract_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real = request.headers.get("x-real-ip")
        if real:
            return real.strip()
        return request.client.host if request.client else "unknown"