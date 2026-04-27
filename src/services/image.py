"""Image utility helpers — encoding, validation, format detection."""

import base64
from typing import Optional

from src.core.constants import SUPPORTED_IMAGE_MIMES


def encode_to_base64(image_data: bytes) -> str:
    return base64.b64encode(image_data).decode("utf-8")


def detect_mime(image_data: bytes) -> str:
    if image_data[:8].startswith(b"\x89PNG"):
        return "image/png"
    if image_data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_data[:4] == b"GIF8":
        return "image/gif"
    if image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def is_valid_image(content_type: str) -> bool:
    return content_type.lower() in SUPPORTED_IMAGE_MIMES


def make_data_url(image_data: bytes) -> str:
    mime = detect_mime(image_data)
    b64 = encode_to_base64(image_data)
    return f"data:{mime};base64,{b64}"
