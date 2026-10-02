"""In-memory rate limiter — limits messages per user within a time window.

NOTE (V9): This is a per-process in-memory store. When running with multiple
uvicorn workers (e.g. --workers 4), each worker has an independent bucket,
making the effective limit N_WORKERS × _DEFAULT_LIMIT per window.

For production multi-worker deployments, replace _buckets with a Redis-backed
store (e.g. redis.incr + EXPIRE) to enforce the limit across all workers.
"""

import threading
import time

# Default: 20 messages per 60 seconds per worker
# Effective limit with 4 workers: up to 80 messages per 60 seconds
_DEFAULT_LIMIT = 20
_DEFAULT_WINDOW = 60  # seconds

_lock = threading.Lock()
_buckets: dict[str, tuple[int, float, int]] = {}  # user_id -> (count, start, window)
_last_cleanup = 0.0


def _cleanup_expired(now: float, minimum_window: int) -> None:
    """Remove idle buckets without shortening a caller's custom window."""
    expired = [
        user_id
        for user_id, (_, start, bucket_window) in _buckets.items()
        if now - start > max(minimum_window, bucket_window)
    ]
    for user_id in expired:
        del _buckets[user_id]


def is_rate_limited(user_id: str, limit: int = _DEFAULT_LIMIT, window: int = _DEFAULT_WINDOW) -> bool:
    """Return True if user has exceeded the rate limit."""
    global _last_cleanup
    now = time.monotonic()
    with _lock:
        if now - _last_cleanup >= _DEFAULT_WINDOW:
            _cleanup_expired(now, _DEFAULT_WINDOW)
            _last_cleanup = now
        count, start, _ = _buckets.get(user_id, (0, now, window))
        if now - start > window:
            # New window
            _buckets[user_id] = (1, now, window)
            return False
        if count >= limit:
            return True
        _buckets[user_id] = (count + 1, start, window)
        return False


def cleanup_expired(window: int = _DEFAULT_WINDOW) -> None:
    """Remove expired entries to prevent memory leak."""
    now = time.monotonic()
    with _lock:
        _cleanup_expired(now, window)
