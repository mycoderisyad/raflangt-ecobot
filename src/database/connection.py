"""PostgreSQL connection pool using psycopg2."""

import logging
from contextlib import contextmanager
from typing import Any, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

from src.config import get_settings

logger = logging.getLogger(__name__)

_pool: Optional[ThreadedConnectionPool] = None


def init_db() -> None:
    """Create the connection pool and run migrations."""
    global _pool
    settings = get_settings()
    _pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=settings.database.url,
    )
    logger.info("PostgreSQL connection pool created")
    _run_migrations()


def _run_migrations() -> None:
    """Execute SQL migration files in order."""
    import pathlib

    migrations_dir = pathlib.Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        return
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        logger.info("Running migration %s", sql_file.name)
        with get_db() as db:
            db.execute_script(sql_file.read_text("utf-8"))


class DB:
    """Thin wrapper around a psycopg2 connection for convenience."""

    def __init__(self, conn):
        self._conn = conn

    def execute_script(self, sql: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(sql)
        self._conn.commit()

    def fetchall(self, query: str, params: tuple = ()) -> List[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    # Alias for snake_case consistency
    fetch_all = fetchall

    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    # Alias for snake_case consistency
    fetch_one = fetchone

    def execute(self, query: str, params: tuple = ()) -> int:
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            self._conn.commit()
            return cur.rowcount


def close_db() -> None:
    """Close the connection pool gracefully."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info("PostgreSQL connection pool closed")


@contextmanager
def get_db():
    """Yield a DB wrapper, returning the connection to the pool afterwards."""
    global _pool
    if _pool is None:
        init_db()
    conn = _pool.getconn()
    try:
        yield DB(conn)
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
