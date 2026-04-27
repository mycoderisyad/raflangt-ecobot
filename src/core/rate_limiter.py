"""In-memory rate limiter — limits messages per user within a time window.

NOTE (V9): This is a per-process in-memory store. When running with multiple
uvicorn workers (e.g. --workers 4), each worker has an independent bucket,
making the effective limit N_WORKERS × _DEFAULT_LIMIT per window.

For production multi-worker deployments, replace _buckets with a Redis-backed
store (e.g. redis.incr + EXPIRE) to enforce the limit across all workers.
"""

import time
import threading
from typing import Dict, Tuple

# Default: 20 messages per 60 seconds per worker
# Effective limit with 4 workers: up to 80 messages per 60 seconds
_DEFAULT_LIMIT = 20
_DEFAULT_WINDOW = 60  # seconds

_lock = threading.Lock()
_buckets: Dict[str, Tuple[int, float]] = {}  # user_id -> (count, window_start)


def is_rate_limited(user_id: str, limit: int = _DEFAULT_LIMIT, window: int = _DEFAULT_WINDOW) -> bool:
    """Return True if user has exceeded the rate limit."""
    now = time.time()
    with _lock:
        count, start = _buckets.get(user_id, (0, now))
        if now - start > window:
            # New window
            _buckets[user_id] = (1, now)
            return False
        if count >= limit:
            return True
        _buckets[user_id] = (count + 1, start)
        return False


def cleanup_expired(window: int = _DEFAULT_WINDOW) -> None:
    """Remove expired entries to prevent memory leak."""
    now = time.time()
    with _lock:
        expired = [k for k, (_, start) in _buckets.items() if now - start > window]
        for k in expired:
            del _buckets[k]
