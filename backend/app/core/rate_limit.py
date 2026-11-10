import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

WINDOW_SECONDS = 60.0


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window: float = WINDOW_SECONDS) -> bool:
        if limit <= 0:
            return True

        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            cutoff = now - window
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = InMemoryRateLimiter()


def rate_limit(scope: str):
    def dependency(request: Request) -> None:
        limit = settings.rate_limit_per_minute
        client = request.client.host if request.client else "unknown"
        if not limiter.allow(f"{scope}:{client}", limit):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak percobaan. Coba lagi dalam satu menit.",
                headers={"Retry-After": "60"},
            )

    return dependency
