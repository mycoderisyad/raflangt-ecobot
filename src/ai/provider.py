"""AI provider abstraction — Gemini & OpenAI via openai SDK."""

import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI

from src.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def get_ai_client() -> OpenAI:
    """Return a singleton OpenAI-compatible client configured for the active provider."""
    global _client
    if _client is None:
        cfg = get_settings().ai
        _client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        logger.info("AI client initialised — provider=%s model=%s", cfg.provider, cfg.model)
    return _client


def chat_completion(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Send a chat completion request and return the assistant text."""
    client = get_ai_client()
    cfg = get_settings().ai
    model = model or cfg.model
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("AI chat completion error: %s", e)
        raise


def chat_completion_with_image(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 1024,
) -> str:
    """Chat completion that may include image content blocks."""
    return chat_completion(messages, model=model, temperature=temperature, max_tokens=max_tokens)
