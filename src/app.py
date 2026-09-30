"""FastAPI application and managed service lifecycles."""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings, init_settings
from src.database import close_db, init_db

_PLACEHOLDERS = {
    "",
    "secret",
    "your-secret-key",
    "change-me-to-a-random-string",
    "change-me-to-something-random",
    "admin",
    "admin123",
}


def _setup_logging(environment: str) -> None:
    Path("logs").mkdir(exist_ok=True)
    level = logging.WARNING if environment == "production" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(Path("logs") / "ecobot.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _validate_settings() -> None:
    cfg = get_settings()
    if cfg.app.jwt_ttl_seconds <= 0:
        raise RuntimeError("JWT_TTL_SECONDS must be greater than zero")
    try:
        ZoneInfo(cfg.app.timezone)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(f"Unknown TIMEZONE: {cfg.app.timezone}") from exc
    weak = (
        cfg.app.api_secret_key.lower() in _PLACEHOLDERS
        or cfg.app.api_secret_key.lower().startswith("replace-with-")
        or len(cfg.app.api_secret_key) < 32
        or cfg.app.admin_password.lower() in _PLACEHOLDERS
        or cfg.app.admin_password.lower().startswith("replace-with-")
        or len(cfg.app.admin_password) < 12
    )
    if cfg.app.environment == "production" and weak:
        raise RuntimeError(
            "Production requires a strong API_SECRET_KEY and ADMIN_PASSWORD in .env"
        )
    if weak:
        logging.getLogger(__name__).warning(
            "Weak local admin/API credentials detected; bind development server to localhost"
        )
    if cfg.telegram.enabled and not cfg.telegram.bot_token:
        raise RuntimeError("TELEGRAM_ENABLED=true requires TELEGRAM_BOT_TOKEN")
    if (
        cfg.telegram.mode == "webhook"
        and cfg.telegram.enabled
        and not cfg.telegram.webhook_secret
    ):
        raise RuntimeError("TELEGRAM_MODE=webhook requires TELEGRAM_WEBHOOK_SECRET")
    if (
        cfg.app.environment == "production"
        and cfg.telegram.mode == "webhook"
        and cfg.telegram.enabled
        and len(cfg.telegram.webhook_secret) < 32
    ):
        raise RuntimeError(
            "Production Telegram webhooks require a random TELEGRAM_WEBHOOK_SECRET of at least 32 characters"
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_settings()
    _setup_logging(get_settings().app.environment)
    _validate_settings()
    init_db()

    from src.services.scheduler import start_scheduler, stop_scheduler
    from src.services.telegram_polling import TelegramPollingWorker

    cfg = get_settings()
    polling_worker = (
        TelegramPollingWorker()
        if cfg.telegram.enabled and cfg.telegram.mode == "polling"
        else None
    )
    try:
        if cfg.telegram.enabled:
            start_scheduler()
        if polling_worker:
            polling_worker.start()
        yield
    finally:
        if polling_worker:
            polling_worker.stop()
        stop_scheduler()
        close_db()


def create_app() -> FastAPI:
    cfg = init_settings().app
    app = FastAPI(
        title=cfg.name,
        version=cfg.version,
        description="Waste management assistant API with Telegram bot and admin endpoints.",
        lifespan=lifespan,
    )
    if cfg.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Telegram-Bot-Api-Secret-Token",
            ],
        )

    from src.api.admin import router as admin_router
    from src.api.auth import router as auth_router
    from src.api.health import router as health_router
    from src.api.webhook_telegram import router as telegram_router

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(telegram_router)
    return app


app = create_app()
