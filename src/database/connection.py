"""PostgreSQL connection pool shared by synchronous services."""

import logging
import threading
from contextlib import contextmanager
from typing import Any, Iterator, Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

from src.config import get_settings

logger = logging.getLogger(__name__)
_pool: Optional[ThreadedConnectionPool] = None
_pool_lock = threading.Lock()


def init_db() -> None:
    """Open the connection pool. Schema migrations are an explicit CLI task."""
    global _pool
    if _pool is not None:
        return
    with _pool_lock:
        if _pool is None:
            _pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=get_settings().database.url,
                connect_timeout=5,
            )
            logger.info("PostgreSQL connection pool created")


class DB:
    """Small adapter that returns rows as dictionaries."""

    def __init__(self, conn):
        self._conn = conn

    def execute_script(self, sql: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(sql)

    def fetchall(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    fetch_all = fetchall

    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict[str, Any]]:
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    fetch_one = fetchone

    def execute(self, query: str, params: tuple = ()) -> int:
        with self._conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount


def close_db() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.closeall()
            _pool = None
            logger.info("PostgreSQL connection pool closed")


@contextmanager
def get_db() -> Iterator[DB]:
    global _pool
    if _pool is None:
        init_db()
    if _pool is None:
        raise RuntimeError("PostgreSQL connection pool is unavailable")
    conn = _pool.getconn()
    try:
        yield DB(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
