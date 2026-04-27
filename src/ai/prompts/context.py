"""Dynamic context injection — fetches relevant DB data to include in prompts."""

import logging
from typing import Dict, Any, List

from src.database.models.collection import CollectionPointModel, CollectionScheduleModel

logger = logging.getLogger(__name__)


def build_db_context(intent: str) -> str:
    """Return a Markdown-formatted string with relevant DB data for the given intent."""
    parts: List[str] = []

    if intent in ("schedule", "chat", "help", "greeting"):
        parts.append(_schedules_context())

    if intent in ("location", "chat", "help", "greeting"):
        parts.append(_locations_context())

    return "\n".join(p for p in parts if p)


def _schedules_context() -> str:
    try:
        model = CollectionScheduleModel()
        schedules = model.get_all_active()
        if not schedules:
            return "Jadwal pengumpulan: belum ada data."
        lines = ["**Jadwal Pengumpulan Sampah:**"]
        for s in schedules:
            lines.append(f"- {s['location_name']} ({s['address']}): {s['schedule_day']} {s['schedule_time']}")
        return "\n".join(lines)
    except Exception as e:
        logger.error("Error loading schedules context: %s", e)
        return ""


def _locations_context() -> str:
    try:
        model = CollectionPointModel()
        points = model.get_all_active()
        if not points:
            return "Titik pengumpulan: belum ada data."
        lines = ["**Titik Pengumpulan Sampah:**"]
        for p in points:
            desc = f"- {p['name']} ({p['type']}): {p.get('description', '')}"
            if p.get("schedule"):
                desc += f" — Jadwal: {p['schedule']}"
            lines.append(desc)
        return "\n".join(lines)
    except Exception as e:
        logger.error("Error loading locations context: %s", e)
        return ""
