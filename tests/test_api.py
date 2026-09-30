from types import SimpleNamespace
import threading

import jwt
from fastapi.testclient import TestClient
import pytest

from src.app import app
from src.api import auth, webhook_telegram
from src.api.schemas import LocationCreate, ScheduleCreate, UserCreate
from src.channels.telegram import TelegramChannel
from src.config import TelegramConfig
from src.services.telegram_polling import TelegramPollingWorker


client = TestClient(app)


def _fake_settings():
    return SimpleNamespace(
        app=SimpleNamespace(
            api_secret_key="test-secret-that-is-long-enough-for-hs256",
            admin_username="admin-test",
            admin_password="password-test",
            jwt_ttl_seconds=3600,
        ),
        telegram=TelegramConfig(
            enabled=True,
            bot_token="fake-token",
            webhook_secret="webhook-secret",
            mode="webhook",
        ),
    )


def test_health_and_openapi_are_public():
    assert client.get("/health").status_code == 200
    assert "/api/v1/auth/login" in client.get("/openapi.json").json()["paths"]


def test_admin_routes_require_bearer_token(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", _fake_settings)
    assert client.get("/api/v1/dashboard").status_code == 401
    assert (
        client.get(
            "/api/v1/dashboard", headers={"Authorization": "Bearer invalid"}
        ).status_code
        == 401
    )


def test_login_returns_signed_token_and_me_endpoint(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", _fake_settings)
    auth._login_attempts.clear()

    bad = client.post(
        "/api/v1/auth/login", json={"username": "admin-test", "password": "wrong"}
    )
    assert bad.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin-test", "password": "password-test"},
    )
    assert response.status_code == 200
    assert response.json()["expires_in"] == 3600
    claims = jwt.decode(
        response.json()["access_token"],
        _fake_settings().app.api_secret_key,
        algorithms=["HS256"],
        issuer="ecobot",
        audience="ecobot-admin",
    )
    assert claims["sub"] == "admin-test"

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json() == {"username": "admin-test", "role": "admin"}


def test_login_is_rate_limited(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", _fake_settings)
    auth._login_attempts.clear()
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"username": "admin-test", "password": "wrong"},
            ).status_code
            == 401
        )
    limited = client.post(
        "/api/v1/auth/login",
        json={"username": "admin-test", "password": "wrong"},
    )
    assert limited.status_code == 429


def test_telegram_webhook_fails_closed_and_processes_valid_secret(monkeypatch):
    monkeypatch.setattr(webhook_telegram, "get_settings", _fake_settings)
    monkeypatch.setattr(webhook_telegram, "process_update", lambda payload: "ok")
    payload = {"update_id": 123, "message": {"text": "hello"}}

    denied = client.post("/webhook/telegram", json=payload)
    assert denied.status_code == 403

    accepted = client.post(
        "/webhook/telegram",
        json=payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "webhook-secret"},
    )
    assert accepted.status_code == 200
    assert accepted.json() == {"status": "ok"}


def test_payload_schemas_reject_invalid_values():
    try:
        UserCreate.model_validate({"user_id": "628xx"})
    except ValueError:
        pass
    else:
        raise AssertionError("non-numeric Telegram chat ID should be rejected")

    try:
        LocationCreate.model_validate(
            {
                "name": "x",
                "type": "TPS",
                "latitude": 91,
                "longitude": 0,
                "accepted_waste_types": ["ORGANIK"],
                "schedule": "Sabtu",
            }
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid location type/coordinates should be rejected")

    try:
        ScheduleCreate.model_validate(
            {
                "location_name": "TPS",
                "address": "Jalan",
                "schedule_day": "Senin",
                "start_time": "25:00",
                "end_time": "26:00",
                "waste_types": ["ORGANIK"],
            }
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid schedule times should be rejected")


def test_telegram_parser_ignores_non_private_chat(monkeypatch):
    monkeypatch.setattr(
        "src.channels.telegram.get_settings",
        lambda: SimpleNamespace(telegram=TelegramConfig()),
    )
    update = {"message": {"chat": {"id": -100, "type": "group"}, "text": "hi"}}
    assert TelegramChannel().parse_webhook(update) is None


def test_polling_refuses_to_start_while_webhook_is_registered(monkeypatch):
    monkeypatch.setattr(
        TelegramChannel,
        "get_webhook_info",
        lambda self: {"url": "https://example.test/hook"},
    )
    with pytest.raises(RuntimeError, match="Telegram masih terpasang"):
        TelegramPollingWorker().start()


def test_polling_worker_starts_and_stops_cleanly(monkeypatch):
    worker = TelegramPollingWorker()
    called = threading.Event()
    monkeypatch.setattr(TelegramChannel, "get_webhook_info", lambda self: {"url": ""})

    def one_empty_poll(self, offset=None, timeout=25):
        called.set()
        worker._stop.set()
        return []

    monkeypatch.setattr(TelegramChannel, "get_updates", one_empty_poll)
    worker.start()
    assert called.wait(timeout=2)
    worker.stop()
    assert worker._thread is not None
    assert not worker._thread.is_alive()
