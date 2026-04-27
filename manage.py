#!/usr/bin/env python3
"""
EcoBot v2 — Database Management CLI

Usage:
  python manage.py db:create    Create the 'ecobot' database
  python manage.py db:migrate   Run all migration files
  python manage.py db:seed      Insert sample / seed data
  python manage.py db:setup     create + migrate + seed (first-time setup)
  python manage.py db:reset     Drop all tables and re-run migrate + seed
  python manage.py db:status    Show connection info and table list
"""

import argparse
import sys
from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.config import init_settings

settings = init_settings()
DATABASE_URL = settings.database.url

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_db_url(url: str) -> dict:
    """Extract components from a PostgreSQL URL."""
    # postgresql://user:pass@host:port/dbname
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "postgres",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "dbname": parsed.path.lstrip("/") or "ecobot",
    }


def _connect_maintenance():
    """Connect to the 'postgres' maintenance DB (for CREATE/DROP DATABASE)."""
    info = _parse_db_url(DATABASE_URL)
    return psycopg2.connect(
        dbname="postgres",
        user=info["user"],
        password=info["password"],
        host=info["host"],
        port=info["port"],
    )


def _connect_app():
    """Connect to the application database."""
    return psycopg2.connect(DATABASE_URL)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def db_create():
    """Create the application database if it doesn't exist."""
    info = _parse_db_url(DATABASE_URL)
    dbname = info["dbname"]

    conn = _connect_maintenance()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    exists = cur.fetchone()

    if exists:
        print(f"  Database '{dbname}' already exists — skipping")
    else:
        cur.execute(f'CREATE DATABASE "{dbname}"')
        print(f"  Database '{dbname}' created")

    cur.close()
    conn.close()


def db_migrate():
    """Run all SQL migration files in order."""
    migrations_dir = Path(__file__).parent / "src" / "database" / "migrations"
    if not migrations_dir.exists():
        print("  No migrations directory found")
        return

    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        print("  No migration files found")
        return

    conn = _connect_app()
    cur = conn.cursor()

    for sql_file in sql_files:
        print(f"  Running {sql_file.name} ...")
        sql = sql_file.read_text("utf-8")
        cur.execute(sql)

    conn.commit()
    cur.close()
    conn.close()
    print(f"  {len(sql_files)} migration(s) applied")


def db_seed():
    """Insert seed / sample data."""
    seed_file = Path(__file__).parent / "src" / "database" / "seed.sql"
    if not seed_file.exists():
        print("  No seed.sql found — skipping")
        return

    conn = _connect_app()
    cur = conn.cursor()
    sql = seed_file.read_text("utf-8")
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("  Seed data inserted")


def db_setup():
    """Full first-time setup: create → migrate → seed."""
    print("[1/3] Creating database ...")
    db_create()
    print("[2/3] Running migrations ...")
    db_migrate()
    print("[3/3] Seeding data ...")
    db_seed()
    print("\nDone! Run: python main.py")


def db_reset():
    """Drop all tables and re-run migrations + seed."""
    print("[1/3] Dropping all tables ...")
    conn = _connect_app()
    cur = conn.cursor()
    cur.execute("""
        DO $$ DECLARE r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("  All tables dropped")

    print("[2/3] Running migrations ...")
    db_migrate()
    print("[3/3] Seeding data ...")
    db_seed()
    print("\nDone! Database reset complete.")


def db_status():
    """Show connection info and list of tables."""
    info = _parse_db_url(DATABASE_URL)
    print(f"  Host     : {info['host']}:{info['port']}")
    print(f"  Database : {info['dbname']}")
    print(f"  User     : {info['user']}")

    try:
        conn = _connect_app()
        cur = conn.cursor()
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()

        if tables:
            print(f"  Tables   : {len(tables)}")
            for t in tables:
                cur2 = _connect_app().cursor()
                cur2.execute(f"SELECT COUNT(*) FROM {t}")
                count = cur2.fetchone()[0]
                cur2.connection.close()
                print(f"             - {t} ({count} rows)")
        else:
            print("  Tables   : (none — run db:migrate)")
    except Exception as e:
        print(f"  Status   : OFFLINE — {e}")


# ---------------------------------------------------------------------------
# Webhook Commands
# ---------------------------------------------------------------------------

def webhook_tg():
    """Register Telegram webhook with Bot API."""
    if not settings.telegram.enabled:
        print("  Telegram is disabled (TELEGRAM_ENABLED=false)")
        return

    token = settings.telegram.bot_token
    if not token:
        print("  ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    public_url = input("  Enter your public URL (e.g. https://abc.ngrok.io): ").strip().rstrip("/")
    if not public_url:
        print("  Cancelled")
        return

    webhook_url = f"{public_url}/webhook/telegram"
    api_url = f"https://api.telegram.org/bot{token}/setWebhook"

    resp = requests.post(api_url, json={"url": webhook_url}, timeout=15)
    data = resp.json()

    if data.get("ok"):
        print(f"  Telegram webhook set → {webhook_url}")
    else:
        print(f"  ERROR: {data.get('description', resp.text)}")

    # Show current info
    info = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10).json()
    result = info.get("result", {})
    print(f"  Current URL        : {result.get('url', '(none)')}")
    print(f"  Pending updates    : {result.get('pending_update_count', 0)}")
    print(f"  Last error         : {result.get('last_error_message', '(none)')}")


def webhook_tg_info():
    """Show current Telegram webhook status."""
    token = settings.telegram.bot_token
    if not token:
        print("  ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    info = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10).json()
    result = info.get("result", {})
    print(f"  URL                : {result.get('url') or '(not set)'}")
    print(f"  Pending updates    : {result.get('pending_update_count', 0)}")
    print(f"  Max connections    : {result.get('max_connections', 40)}")
    print(f"  Last error         : {result.get('last_error_message') or '(none)'}")
    print(f"  Last error date    : {result.get('last_error_date') or '(none)'}")


def webhook_tg_delete():
    """Remove Telegram webhook (switch to polling mode)."""
    token = settings.telegram.bot_token
    if not token:
        print("  ERROR: TELEGRAM_BOT_TOKEN not set")
        return

    resp = requests.post(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=10).json()
    if resp.get("ok"):
        print("  Telegram webhook removed")
    else:
        print(f"  ERROR: {resp.get('description', '')}")


def webhook_wa():
    """Show WAHA webhook setup instructions."""
    cfg = settings.whatsapp
    if not cfg.enabled:
        print("  WhatsApp is disabled (WHATSAPP_ENABLED=false)")
        return

    print("  WAHA webhook is configured from the WAHA dashboard / config.")
    print()
    print("  Steps:")
    print("  1. Open your WAHA dashboard (usually http://localhost:3000)")
    print("  2. Go to Sessions → your session → Webhooks")
    print("  3. Add a webhook URL pointing to your EcoBot server:")
    print()

    public_url = input("  Enter your public URL (or press Enter to skip): ").strip().rstrip("/")
    if public_url:
        print(f"\n  Set this as your WAHA webhook URL:")
        print(f"  → {public_url}/webhook/whatsapp")
    else:
        print(f"\n  Webhook endpoint: <YOUR_PUBLIC_URL>/webhook/whatsapp")

    print()
    print(f"  WAHA Base URL  : {cfg.base_url or '(not set)'}")
    print(f"  WAHA Session   : {cfg.session_name}")
    print(f"  Events to use  : message, message.any")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = {
    "db:create": db_create,
    "db:migrate": db_migrate,
    "db:seed": db_seed,
    "db:setup": db_setup,
    "db:reset": db_reset,
    "db:status": db_status,
    "webhook:tg": webhook_tg,
    "webhook:tg:info": webhook_tg_info,
    "webhook:tg:delete": webhook_tg_delete,
    "webhook:wa": webhook_wa,
}


def main():
    parser = argparse.ArgumentParser(
        description="EcoBot v2 — Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {cmd:16s}" for cmd in COMMANDS),
    )
    parser.add_argument("command", choices=COMMANDS.keys(), help="Command to run")
    args = parser.parse_args()

    print(f"\n manage.py {args.command}\n")
    try:
        COMMANDS[args.command]()
    except Exception as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)
    print()


if __name__ == "__main__":
    main()
