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


def _format_waste_types(raw) -> str:
    """Convert JSONB waste_types to readable string."""
    if isinstance(raw, list):
        return ", ".join(raw)
    if isinstance(raw, str):
        try:
            import json
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return ", ".join(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        return raw
    return str(raw) if raw else ""


def _schedules_context() -> str:
    try:
        model = CollectionScheduleModel()
        schedules = model.get_all_active()
        if not schedules:
            return "Jadwal pengumpulan: belum ada data."
        lines = ["Jadwal Pengumpulan Sampah:"]
        for s in schedules:
            wt = _format_waste_types(s.get("waste_types"))
            contact = s.get("contact") or ""
            line = f"- {s['schedule_day']} {s['schedule_time']}: {s['location_name']}, {s['address']}"
            if wt:
                line += f" (jenis: {wt})"
            if contact:
                line += f" — PJ: {contact}"
            lines.append(line)
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
        lines = ["Titik Pengumpulan Sampah:"]
        for p in points:
            wt = _format_waste_types(p.get("accepted_waste_types"))
            desc = p.get("description") or ""
            line = f"- {p['name']} ({p['type']})"
            if desc:
                line += f": {desc}"
            if p.get("schedule"):
                line += f" — Jadwal: {p['schedule']}"
            if wt:
                line += f" — Jenis: {wt}"
            lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        logger.error("Error loading locations context: %s", e)
        return ""
