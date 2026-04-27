"""System prompt builder — composes final prompt from template files + dynamic context."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_cache: Dict[str, str] = {}


def _load_template(name: str) -> str:
    if name not in _cache:
        path = _TEMPLATES_DIR / name
        if path.exists():
            _cache[name] = path.read_text("utf-8")
        else:
            logger.warning("Prompt template not found: %s", name)
            _cache[name] = ""
    return _cache[name]


def build_system_prompt(
    user_name: str = "",
    user_role: str = "warga",
    intent: str = "chat",
    db_context: str = "",
    village_name: str = "",
) -> str:
    """Compose a full system prompt from template parts + dynamic context."""
    parts: List[str] = []

    # 1. Base prompt (always)
    parts.append(_load_template("base.md"))

    # 2. Feature-specific prompt
    if intent == "image_analysis":
        parts.append(_load_template("image_analysis.md"))
    elif intent in ("education", "chat", "schedule", "location"):
        parts.append(_load_template("waste_expert.md"))

    # 3. Admin prompt if admin role
    if user_role == "admin":
        parts.append(_load_template("admin.md"))

    # 4. Dynamic context
    ctx_parts: List[str] = ["## Konteks Saat Ini"]
    if user_name:
        ctx_parts.append(f"- Nama user: {user_name}")
    ctx_parts.append(f"- Role user: {user_role}")
    if village_name:
        ctx_parts.append(f"- Desa/Wilayah: {village_name}")
    if db_context:
        ctx_parts.append(f"\n### Data dari Database\n{db_context}")

    parts.append("\n".join(ctx_parts))

    return "\n\n".join(p for p in parts if p.strip())
