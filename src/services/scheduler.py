"""Background scheduler for automated tasks like collection reminders."""

import json
import logging
import threading
from datetime import datetime

from src.database.models.collection import CollectionScheduleModel
from src.database.models.user import UserModel
from src.channels.telegram import TelegramChannel
from src.config import get_settings

logger = logging.getLogger(__name__)

# Indonesian day names matching the DB constraint
_DAY_MAP = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}

_scheduler_thread = None
_stop_event = threading.Event()


def start_scheduler() -> None:
    """Start the background reminder scheduler (runs every 60 s)."""
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_loop, daemon=True, name="ecobot-scheduler")
    _scheduler_thread.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    _stop_event.set()
    logger.info("Scheduler stopping")


# Track which (day, time) combos we already sent today so we don't spam
_sent_today: set = set()
_last_reset_date: str = ""


def _loop() -> None:
    """Main scheduler loop — checks every 60 seconds."""
    import time as _time

    while not _stop_event.is_set():
        try:
            _tick()
        except Exception as e:
            logger.error("Scheduler tick error: %s", e, exc_info=True)
        _stop_event.wait(60)


def _tick() -> None:
    global _last_reset_date, _sent_today

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    day_name = _DAY_MAP.get(now.weekday(), "")

    # Reset sent set at midnight
    if today_str != _last_reset_date:
        _sent_today = set()
        _last_reset_date = today_str

    if not day_name:
        return

    cfg = get_settings()
    if not cfg.telegram.enabled:
        return

    schedule_model = CollectionScheduleModel()
    schedules = schedule_model.get_by_day(day_name)

    if not schedules:
        return

    for sched in schedules:
        sched_time = sched.get("schedule_time", "")
        sched_key = f"{day_name}_{sched_time}_{sched.get('id')}"

        if sched_key in _sent_today:
            continue

        # Send reminder 30 minutes before (or at the scheduled time)
        if not _should_remind(current_time, sched_time):
            continue

        _sent_today.add(sched_key)
        _send_reminder(sched, cfg)


def _should_remind(current_time: str, sched_time: str) -> bool:
    """Return True if current_time is within 30 minutes before sched_time."""
    try:
        ch, cm = map(int, current_time.split(":"))
        sh, sm = map(int, sched_time.split(":"))
        current_mins = ch * 60 + cm
        sched_mins = sh * 60 + sm
        diff = sched_mins - current_mins
        return 0 <= diff <= 30
    except (ValueError, AttributeError):
        return False


def _send_reminder(sched: dict, cfg) -> None:
    """Send a reminder message to all active users."""
    try:
        location = sched.get("location_name", "")
        address = sched.get("address", "")
        sched_time = sched.get("schedule_time", "")
        waste_types_raw = sched.get("waste_types", [])

        if isinstance(waste_types_raw, str):
            try:
                waste_types_raw = json.loads(waste_types_raw)
            except (json.JSONDecodeError, TypeError):
                waste_types_raw = [waste_types_raw]

        waste_str = ", ".join(waste_types_raw) if isinstance(waste_types_raw, list) else str(waste_types_raw)

        message = (
            f"Pengingat Pengumpulan Sampah\n\n"
            f"Lokasi: {location}\n"
            f"Alamat: {address}\n"
            f"Waktu: {sched_time}\n"
            f"Jenis: {waste_str}\n\n"
            f"Jangan lupa siapkan sampahmu yang sudah dipilah!"
        )

        user_model = UserModel()
        phones = user_model.get_reminder_enabled_phones()

        if not phones:
            return

        # Only send via Telegram for now (users stored as chat_id for TG)
        if cfg.telegram.enabled:
            tg = TelegramChannel()
            sent = 0
            for phone in phones:
                # Telegram chat IDs are numeric strings
                if phone.isdigit():
                    if tg.send_message(phone, message):
                        sent += 1
            logger.info("Reminder sent to %d/%d Telegram users for %s at %s", sent, len(phones), location, sched_time)

    except Exception as e:
        logger.error("Reminder send error: %s", e, exc_info=True)
