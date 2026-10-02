"""Waste preparation recommendations grounded in EcoBot's active locations and schedules."""

import json
import logging
from typing import Any

from src.database.models.collection import CollectionPointModel, CollectionScheduleModel

logger = logging.getLogger(__name__)

_PREPARATION = {
    "ORGANIK": "Pisahkan dari plastik dan tiriskan cairannya. Jika memungkinkan, olah sisa makanan dan daun menjadi kompos.",
    "ANORGANIK": "Kosongkan, bilas bila perlu, lalu keringkan. Pisahkan plastik, kertas, kaca, dan logam; lipat kardus agar ringkas.",
    "B3": "Pisahkan dari sampah rumah tangga. Simpan tertutup dan jangan dibakar, dibongkar, atau dibuang ke saluran air.",
}


def _as_types(raw: Any) -> set[str]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raw = [raw]
    if not isinstance(raw, list):
        return set()
    return {str(value).strip().upper() for value in raw if str(value).strip()}


def build_waste_recommendation(waste_type: str) -> str:
    normalized = waste_type.strip().upper()
    prep = _PREPARATION.get(normalized)
    if not prep:
        return "\n\nGua belum cukup yakin jenis sampahnya. Coba kirim foto yang lebih dekat dan terlihat jelas."

    lines = [f"\n\nSaran untuk {normalized}: {prep}"]
    try:
        points = CollectionPointModel().get_all_active()
        schedules = CollectionScheduleModel().get_all_active()
    except Exception:
        logger.exception("Could not load collection data for waste recommendation")
        return "".join(lines) + "\nData titik dan jadwal EcoBot sedang tidak bisa dibuka. Konfirmasi dulu ke pengurus."

    matching_points = [point for point in points if normalized in _as_types(point.get("accepted_waste_types"))]
    matching_schedules = [schedule for schedule in schedules if normalized in _as_types(schedule.get("waste_types"))]
    if matching_points:
        lines.append("\nTitik penerimaan dari data EcoBot:")
        for point in matching_points[:3]:
            map_url = (
                f"https://maps.google.com/?q={point['latitude']},{point['longitude']}"
            )
            lines.append(
                f"\n- {point['name']} — {point.get('schedule') or 'jadwal belum dicatat'}"
                f" — {map_url}"
            )
    else:
        lines.append("\nBelum ada titik di data EcoBot yang mencatat menerima jenis ini; cek dulu ke pengurus.")

    if matching_schedules:
        lines.append("\nJadwal pengumpulan:")
        for schedule in matching_schedules[:3]:
            lines.append(
                f"\n- {schedule['location_name']} — {schedule['schedule_day']} "
                f"{schedule['schedule_time']} ({schedule['address']})"
            )
    elif not matching_points:
        lines.append("\nJadwal khusus untuk jenis ini belum tersedia di data EcoBot.")
    return "".join(lines)
