"""Phone number normalization utilities."""

import re


def normalize_phone(phone: str) -> str:
    """Return phone in +62xxx format (display / Telegram)."""
    if not phone:
        return phone
    phone = phone.replace("@c.us", "").replace("@s.whatsapp.net", "")
    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("+62"):
        return phone
    if phone.startswith("62"):
        return "+" + phone
    if phone.startswith("0"):
        return "+62" + phone[1:]
    return phone


def normalize_phone_for_db(phone: str) -> str:
    """Return phone in 62xxx@c.us format (WhatsApp DB key)."""
    clean = phone.replace("@c.us", "").replace("@s.whatsapp.net", "")
    clean = re.sub(r"[^\d+]", "", clean)
    if clean.startswith("+62"):
        clean = clean[1:]
    elif clean.startswith("0"):
        clean = "62" + clean[1:]
    if clean and not clean.endswith("@c.us"):
        return clean + "@c.us"
    return clean


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return False
    clean = normalize_phone(phone)
    if clean.startswith("+62"):
        digits = clean[3:]
        return 8 <= len(digits) <= 13 and digits.isdigit()
    return False
