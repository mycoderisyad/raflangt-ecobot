from src.core import rate_limiter


def test_rate_limiter_reclaims_idle_users_without_changing_active_limit(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(rate_limiter.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(rate_limiter, "_buckets", {})
    monkeypatch.setattr(rate_limiter, "_last_cleanup", 0.0)

    assert not rate_limiter.is_rate_limited("idle", limit=1)
    assert not rate_limiter.is_rate_limited("active", limit=1)
    assert rate_limiter.is_rate_limited("active", limit=1)

    clock[0] = 61.0
    assert not rate_limiter.is_rate_limited("active", limit=1)
    assert "idle" not in rate_limiter._buckets
    assert rate_limiter.is_rate_limited("active", limit=1)


def test_rate_limiter_keeps_custom_window_during_cleanup(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(rate_limiter.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(rate_limiter, "_buckets", {})
    monkeypatch.setattr(rate_limiter, "_last_cleanup", 0.0)

    assert not rate_limiter.is_rate_limited("long_window", limit=1, window=120)
    clock[0] = 61.0
    assert not rate_limiter.is_rate_limited("other")
    assert rate_limiter.is_rate_limited("long_window", limit=1, window=120)

    clock[0] = 121.0
    assert not rate_limiter.is_rate_limited("long_window", limit=1, window=120)
