"""Text formatting helpers."""


def ensure_length_limit(text: str, max_length: int = 4096) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
