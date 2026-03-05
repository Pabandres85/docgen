import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


@dataclass
class RateLimitConfig:
    max_requests: int
    window_seconds: int


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: RateLimitConfig):
        super().__init__(app)
        self.config = config
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        host = request.client.host if request.client else "unknown"
        return host

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/ready", "/docs", "/openapi.json"}:
            return await call_next(request)

        now = time.time()
        key = self._client_key(request)
        window = self.config.window_seconds
        limit = self.config.max_requests

        with self._lock:
            hit_queue = self._hits[key]
            cutoff = now - window
            while hit_queue and hit_queue[0] < cutoff:
                hit_queue.popleft()
            if len(hit_queue) >= limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(window)},
                )
            hit_queue.append(now)

        return await call_next(request)
