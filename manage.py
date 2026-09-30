#!/usr/bin/env python3
"""Database and Telegram management commands for local development."""

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
import psycopg2.sql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.config import init_settings

settings = init_settings()
DATABASE_URL = settings.database.url
MIGRATIONS = ROOT / "src" / "database" / "migrations"


def _db_parts() -> dict[str, str | int]:
    parsed = urlparse(DATABASE_URL)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "postgres",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/") or "ecobot",
    }


def _connect_app():
    return psycopg2.connect(DATABASE_URL, connect_timeout=5)


def db_create() -> None:
    parts = _db_parts()
    conn = psycopg2.connect(
        dbname="postgres",
        connect_timeout=5,
        **{k: v for k, v in parts.items() if k != "dbname"},
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (parts["dbname"],)
            )
            if cur.fetchone():
                print(f"Database '{parts['dbname']}' already exists")
            else:
                cur.execute(
                    psycopg2.sql.SQL("CREATE DATABASE {} ").format(
                        psycopg2.sql.Identifier(parts["dbname"])
                    )
                )
                print(f"Database '{parts['dbname']}' created")
    finally:
        conn.close()


def db_migrate() -> None:
    conn = _connect_app()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """CREATE TABLE IF NOT EXISTS schema_migrations (
                           migration_name TEXT PRIMARY KEY,
                           applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                       )"""
                )
                cur.execute("SELECT migration_name FROM schema_migrations")
                applied = {row[0] for row in cur.fetchall()}
                for migration in sorted(MIGRATIONS.glob("*.sql")):
                    if migration.name in applied:
                        continue
                    print(f"Applying {migration.name}")
                    cur.execute(migration.read_text(encoding="utf-8"))
                    cur.execute(
                        "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                        (migration.name,),
                    )
        print("Database migrations are up to date")
    finally:
        conn.close()


def db_seed() -> None:
    seed_file = ROOT / "src" / "database" / "seed.sql"
    conn = _connect_app()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(seed_file.read_text(encoding="utf-8"))
        print("Seed data is present")
    finally:
        conn.close()


def db_setup() -> None:
    db_create()
    db_migrate()
    db_seed()
    print("Setup complete. Run: python main.py")


def db_status() -> None:
    parts = _db_parts()
    conn = _connect_app()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
            )
            tables = [row[0] for row in cur.fetchall()]
            print(f"Database: {parts['dbname']} @ {parts['host']}:{parts['port']}")
            for table in tables:
                cur.execute(
                    psycopg2.sql.SQL("SELECT COUNT(*) FROM {}").format(
                        psycopg2.sql.Identifier(table)
                    )
                )
                print(f"  {table}: {cur.fetchone()[0]}")
            if not tables:
                print("No tables. Run: python manage.py db:migrate")
    finally:
        conn.close()


def _telegram_channel():
    cfg = settings.telegram
    if not cfg.enabled or not cfg.bot_token:
        raise RuntimeError("Set TELEGRAM_ENABLED=true and TELEGRAM_BOT_TOKEN in .env")
    from src.channels.telegram import TelegramChannel

    return TelegramChannel()


def telegram_check() -> None:
    bot = _telegram_channel().get_me()
    print(f"Telegram API connected: @{bot.get('username')} (id={bot.get('id')})")


def telegram_webhook_set(url: str | None) -> None:
    bot = _telegram_channel()
    target = (url or input("Public HTTPS URL: ")).strip().rstrip("/")
    if not target.startswith("https://"):
        raise RuntimeError("Telegram webhook requires a public HTTPS URL")
    if not settings.telegram.webhook_secret:
        raise RuntimeError("Set TELEGRAM_WEBHOOK_SECRET in .env")
    bot.set_webhook(f"{target}/webhook/telegram", settings.telegram.webhook_secret)
    print(f"Webhook registered: {target}/webhook/telegram")


def telegram_webhook_info() -> None:
    info = _telegram_channel().get_webhook_info()
    print(f"URL: {info.get('url') or '(not set)'}")
    print(f"Pending updates: {info.get('pending_update_count', 0)}")
    print(f"Last error: {info.get('last_error_message') or '(none)'}")


def telegram_webhook_delete() -> None:
    _telegram_channel().delete_webhook()
    print("Webhook removed; pending updates were preserved")


COMMANDS = {
    "db:create": db_create,
    "db:migrate": db_migrate,
    "db:seed": db_seed,
    "db:setup": db_setup,
    "db:status": db_status,
    "telegram:check": telegram_check,
    "telegram:webhook:info": telegram_webhook_info,
    "telegram:webhook:delete": telegram_webhook_delete,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="EcoBot management CLI")
    parser.add_argument("command", choices=[*COMMANDS, "telegram:webhook:set"])
    parser.add_argument(
        "url", nargs="?", help="Public HTTPS base URL for webhook registration"
    )
    args = parser.parse_args()
    try:
        if args.command == "telegram:webhook:set":
            telegram_webhook_set(args.url)
        else:
            COMMANDS[args.command]()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
