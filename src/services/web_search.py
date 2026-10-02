"""Budgeted web search for time-sensitive environmental questions."""

import logging
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from src.config import get_settings
from src.database.connection import get_db

logger = logging.getLogger(__name__)
SEARCH_URL = "https://api.search.brave.com/res/v1/llm/context"

_TOPIC = re.compile(
    r"\b(sampah|limbah|daur ulang|recycle|plastik|kompos|b3|lingkungan|polusi|"
    r"pencemaran|emisi|iklim|bank sampah|tps|tpst|tpa|ewaste|e-waste)\b",
    re.I,
)
_FRESH = re.compile(
    r"\b(terbaru|terkini|saat ini|sekarang|hari ini|minggu ini|bulan ini|"
    r"tahun ini|update|berita|kabar|aturan baru|regulasi baru|harga|"
    r"cari(?:kan)?(?: di)? (?:internet|web|google)|search|browsing)\b",
    re.I,
)
_LOCAL = re.compile(r"\b(jadwal|lokasi|titik pengumpulan)\b", re.I)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    description: str


def should_search(message: str, intent: str) -> bool:
    """Use a deterministic gate, avoiding a second LLM call per message."""
    if intent in {"schedule", "location", "settings", "registration", "greeting", "help"}:
        return False
    if _LOCAL.search(message) and not re.search(r"\b(berita|aturan|regulasi)\b", message, re.I):
        return False
    return bool(_TOPIC.search(message) and _FRESH.search(message))


class SearchLimitReached(Exception):
    pass


def _reserve_search(user_id: str, daily_limit: int, user_daily_limit: int) -> bool:
    """Atomically reserve one request across workers; failed requests still use quota."""
    if daily_limit <= 0 or user_daily_limit <= 0:
        return False
    try:
        with get_db() as db:
            for bucket, limit in (("global", daily_limit), (f"user:{user_id}", user_daily_limit)):
                row = db.fetchone(
                    """INSERT INTO web_search_quota (usage_day, bucket, request_count)
                       VALUES ((NOW() AT TIME ZONE 'Asia/Jakarta')::date, %s, 1)
                       ON CONFLICT (usage_day, bucket) DO UPDATE
                       SET request_count = web_search_quota.request_count + 1
                       WHERE web_search_quota.request_count < %s
                       RETURNING request_count""",
                    (bucket, limit),
                )
                if row is None:
                    raise SearchLimitReached()
        return True
    except SearchLimitReached:
        return False


def search_web(query: str, user_id: str) -> tuple[str, list[SearchResult]]:
    """Return (status, results). No result content is cached or written to storage."""
    config = get_settings().web_search
    if not config.api_key:
        logger.info("Web search skipped: API key is not configured")
        return "disabled", []
    try:
        if not _reserve_search(user_id, config.daily_limit, config.user_daily_limit):
            logger.info("Web search skipped: daily quota reached")
            return "limited", []
        safe_query = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "", query)
        safe_query = re.sub(r"(?<!\d)(?:\+?62|0)\d[\d\s-]{7,}\d(?!\d)", "", safe_query)
        params = {
            "q": safe_query[:300],
            "country": "ID",
            "count": 5,
            "maximum_number_of_urls": 3,
            "maximum_number_of_tokens": 2048,
            "context_threshold_mode": "balanced",
            "safesearch": "strict",
        }
        if re.search(r"\b(hari ini|24 jam terakhir)\b", query, re.I):
            params["freshness"] = "pd"
        elif re.search(r"\b(minggu ini|7 hari terakhir)\b", query, re.I):
            params["freshness"] = "pw"
        elif re.search(r"\b(bulan ini|30 hari terakhir)\b", query, re.I):
            params["freshness"] = "pm"
        response = requests.get(
            SEARCH_URL,
            headers={"X-Subscription-Token": config.api_key, "Accept": "application/json"},
            params=params,
            timeout=7,
        )
        response.raise_for_status()
        payload = response.json()
        results = []
        generic = payload.get("grounding", {}).get("generic", [])
        for item in generic:
            url = item.get("url", "")
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                continue
            snippets = item.get("snippets", [])
            description = " ".join(
                str(snippet).strip() for snippet in snippets if str(snippet).strip()
            )
            results.append(SearchResult(
                title=str(item.get("title", ""))[:120],
                url=url,
                description=description[:700],
            ))
        status = "ok" if results else "empty"
        logger.info("Web search finished: status=%s sources=%d", status, len(results[:3]))
        return status, results[:3]
    except Exception as exc:
        logger.warning("Web search failed: %s", exc)
        return "error", []
