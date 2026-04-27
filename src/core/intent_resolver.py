"""LLM-based intent classification — replaces regex command parsing."""

import json
import logging
from typing import Dict, Any

from src.ai.provider import chat_completion

logger = logging.getLogger(__name__)

INTENT_PROMPT = """Kamu adalah classifier intent untuk chatbot pengelolaan sampah bernama EcoBot.

Berdasarkan pesan user di bawah, tentukan intent-nya. Balas HANYA dengan JSON (tanpa markdown fence):
{"intent": "<intent>", "confidence": <0.0-1.0>}

Intent yang valid:
- "greeting" — sapaan/salam (halo, hi, selamat pagi, dll)
- "help" — bertanya tentang fitur/menu/kemampuan bot
- "education" — bertanya tentang edukasi sampah, tips, cara daur ulang
- "schedule" — bertanya tentang jadwal pengumpulan sampah
- "location" — bertanya tentang lokasi/titik pengumpulan sampah
- "statistics" — meminta data statistik (khusus koordinator/admin)
- "report" — meminta generate laporan/report (khusus koordinator/admin)
- "registration" — ingin mendaftar
- "chat" — percakapan umum / tidak jelas kategorinya

Pesan user: """

# Fallback mapping for when AI is unavailable
KEYWORD_MAP = {
    "greeting": ["halo", "hai", "hi", "hello", "hey", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum"],
    "help": ["menu", "bantuan", "help", "fitur", "layanan", "bisa apa"],
    "education": ["edukasi", "tips", "belajar", "daur ulang", "kompos", "recycle", "sampah organik", "sampah anorganik"],
    "schedule": ["jadwal", "schedule", "waktu", "pengumpulan", "kapan"],
    "location": ["lokasi", "maps", "peta", "titik", "tempat", "dimana", "di mana"],
    "statistics": ["statistik", "stats", "data", "analytics"],
    "report": ["laporan", "report", "email", "pdf"],
    "registration": ["daftar", "register", "signup"],
}


def resolve_intent(message: str, use_ai: bool = True) -> Dict[str, Any]:
    """Classify user message into an intent.

    Returns {"intent": str, "confidence": float}.
    """
    if use_ai:
        try:
            raw = chat_completion(
                messages=[{"role": "user", "content": INTENT_PROMPT + message}],
                temperature=0.1,
                max_tokens=100,
            )
            # Try to parse JSON from response
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            result = json.loads(raw)
            if "intent" in result:
                return {"intent": result["intent"], "confidence": float(result.get("confidence", 0.8))}
        except Exception as e:
            logger.warning("AI intent resolution failed, falling back to keywords: %s", e)

    # Keyword fallback
    lower = message.strip().lower()
    for intent, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in lower:
                return {"intent": intent, "confidence": 0.6}

    return {"intent": "chat", "confidence": 0.5}
