#!/usr/bin/env python3
"""
EcoBot v2 — Entry Point
Run with: python main.py [--production]
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.app import create_app, create_asgi_app


def main():
    parser = argparse.ArgumentParser(description="EcoBot Launcher")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (default: development)",
    )
    args = parser.parse_args()

    if args.production:
        os.environ["ENVIRONMENT"] = "production"

    # Build the app (initialises settings, db, blueprints)
    create_app()

    from src.config import get_settings

    settings = get_settings()
    port = settings.app.port
    is_dev = settings.app.environment == "development"

    if is_dev:
        print("=" * 50)
        print("EcoBot v2 — Waste Management Assistant")
        print("=" * 50)
        print(f"  Environment : {settings.app.environment}")
        print(f"  AI Provider : {settings.ai.provider}")
        print(f"  WhatsApp    : {'enabled' if settings.whatsapp.enabled else 'disabled'}")
        print(f"  Telegram    : {'enabled' if settings.telegram.enabled else 'disabled'}")
        print(f"  Server      : http://localhost:{port}")
        print("=" * 50)
    else:
        print(f"[INFO] EcoBot started — env={settings.app.environment} port={port}")

    uvicorn.run(
        "src.app:create_asgi_app",
        factory=True,
        host="0.0.0.0",
        port=port,
        reload=is_dev,
        workers=1 if is_dev else 4,
        log_level="info" if is_dev else "warning",
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEcoBot stopped")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
