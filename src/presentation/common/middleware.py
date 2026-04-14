"""Базовые middleware production hardening слоя."""

from __future__ import annotations

from collections import defaultdict, deque
from time import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Прокидывает correlation_id в request state и response header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Request-Id", str(uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = correlation_id
        return response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Простой in-memory rate limiter для чувствительных API endpoints."""

    def __init__(self, app, *, limit_per_minute: int, enabled: bool = True) -> None:
        super().__init__(app)
        self._limit = limit_per_minute
        self._enabled = enabled
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._protected_prefixes = ("/patient/results", "/operator/cards")

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled or not request.url.path.startswith(self._protected_prefixes):
            return await call_next(request)

        key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
        now = time()
        window_start = now - 60
        bucket = self._hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self._limit:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "rate_limited",
                    "message": "Слишком много запросов. Повторите позже.",
                    "correlation_id": getattr(request.state, "correlation_id", str(uuid4())),
                },
            )

        bucket.append(now)
        return await call_next(request)
