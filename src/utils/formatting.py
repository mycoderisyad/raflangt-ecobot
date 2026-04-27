"""Text formatting helpers."""

import re


def ensure_length_limit(text: str, max_length: int = 4096) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def md_to_telegram_html(text: str) -> str:
    """Convert common Markdown to Telegram-safe HTML.

    Handles: **bold**, *italic*, `code`, ```pre```, [link](url)
    Escapes HTML entities first so raw user text is safe.
    """
    # Escape HTML entities
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Code blocks (``` ... ```)
    text = re.sub(r"```(?:\w*)\n?(.*?)```", r"<pre>\1</pre>", text, flags=re.DOTALL)

    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # Italic: *text* or _text_  (but not inside <b> tags from above)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+?)_(?!\w)", r"<i>\1</i>", text)

    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # Headings (## Heading) → bold line
    text = re.sub(r"^#{1,3}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Bullet lists: standardize  •/*/- at start of line → •
    text = re.sub(r"^[\*\-]\s+", "• ", text, flags=re.MULTILINE)

    # Numbered list: keep as-is, just ensure space
    text = re.sub(r"^(\d+)\.\s+", r"\1. ", text, flags=re.MULTILINE)

    return text.strip()
