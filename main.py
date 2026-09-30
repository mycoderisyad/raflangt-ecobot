"""Local launcher. Use one worker because Telegram polling and reminders are in-process."""

import argparse
import os

from dotenv import load_dotenv


def main() -> None:
    parser = argparse.ArgumentParser(description="EcoBot FastAPI launcher")
    parser.add_argument(
        "--production", action="store_true", help="Run with production settings"
    )
    args = parser.parse_args()
    load_dotenv()
    if args.production:
        os.environ["ENVIRONMENT"] = "production"

    import uvicorn
    from src.config import init_settings

    settings = init_settings()
    is_dev = settings.app.environment == "development"
    print(
        f"EcoBot API — env={settings.app.environment} port={settings.app.port} telegram={settings.telegram.mode}"
    )
    uvicorn.run(
        "src.app:app",
        host="127.0.0.1" if is_dev else "0.0.0.0",
        port=settings.app.port,
        reload=is_dev,
        workers=1,
        log_level="info" if is_dev else "warning",
    )


if __name__ == "__main__":
    main()
