"""Flask application factory + ASGI wrapper for uvicorn."""

import atexit
import logging
import sys
from pathlib import Path

from flask import Flask
from dotenv import load_dotenv
from asgiref.wsgi import WsgiToAsgi

from src.config import init_settings, get_settings
from src.database import init_db, close_db


_PLACEHOLDER_SECRETS = {
    "change-me-to-a-random-string",
    "change-me-to-something-random",
    "your-secret-key",
    "secret",
    "",
}


def _check_secrets(environment: str) -> None:
    """In production, abort if any critical secret is a known placeholder."""
    if environment != "production":
        return
    import os as _os
    checks = {
        "API_SECRET_KEY": _os.getenv("API_SECRET_KEY", ""),
        "ADMIN_PANEL_SECRET_KEY": _os.getenv("ADMIN_PANEL_SECRET_KEY", ""),
        "ADMIN_PANEL_PASSWORD": _os.getenv("ADMIN_PANEL_PASSWORD", ""),
    }
    for name, value in checks.items():
        if value in _PLACEHOLDER_SECRETS or value == "admin":
            raise RuntimeError(
                f"SECURITY ERROR: {name} is set to a weak/placeholder value. "
                "Set a strong random secret before running in production."
            )


def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()

    settings = init_settings()
    _check_secrets(settings.app.environment)
    _setup_logging(settings.app.environment)

    # Initialise database pool
    init_db()

    app = Flask(__name__)
    app.config["DEBUG"] = settings.app.debug

    # Register blueprints
    from src.api import health_bp, wa_webhook_bp, tg_webhook_bp, users_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(wa_webhook_bp)
    app.register_blueprint(tg_webhook_bp)
    app.register_blueprint(users_bp)

    # Start background scheduler for reminders
    from src.services.scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    # Graceful shutdown
    atexit.register(stop_scheduler)
    atexit.register(close_db)

    logger = logging.getLogger(__name__)
    logger.info("EcoBot %s started — env=%s", settings.app.version, settings.app.environment)

    return app


def create_asgi_app():
    """ASGI entry point for uvicorn (production)."""
    return WsgiToAsgi(create_app())


def _setup_logging(environment: str) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = logging.WARNING if environment == "production" else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    handlers = [
        logging.FileHandler(log_dir / "ecobot.log"),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(level=level, format=fmt, handlers=handlers)

    if environment == "production":
        for lib in ("werkzeug", "urllib3", "requests"):
            logging.getLogger(lib).setLevel(logging.ERROR)
