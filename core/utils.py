"""
Core Utilities
"""

import re
import logging
from typing import Optional, Dict, Any


class PhoneNumberUtils:
    """Phone number utilities"""

    @staticmethod
    def normalize(phone_number: str) -> str:
        """Normalize phone number by removing +, @c.us, and whitespace"""
        if not phone_number:
            return ""

        # Remove @c.us suffix if present
        if "@c.us" in phone_number:
            phone_number = phone_number.replace("@c.us", "")

        # Remove + prefix if present
        if phone_number.startswith("+"):
            phone_number = phone_number[1:]

        return phone_number.strip()

    @staticmethod
    def validate(phone_number: str) -> bool:
        """Validate phone number format"""
        normalized = PhoneNumberUtils.normalize(phone_number)
        return bool(re.match(r"^\d{10,15}$", normalized))


class MessageFormatter:
    """Message formatting utilities for user-friendly responses"""

    @staticmethod
    def format_welcome_header(title: str) -> str:
        """Format welcome message header"""
        return f"🤖 {title}\n{'─' * 35}\n\n"

    @staticmethod
    def format_info_header(title: str) -> str:
        """Format information message header"""
        return f"ℹ️ {title}\n{'─' * 35}\n\n"

    @staticmethod
    def format_success_header(title: str) -> str:
        """Format success message header"""
        return f"✅ {title}\n{'─' * 35}\n\n"

    @staticmethod
    def format_registration_form() -> str:
        """Format registration form template"""
        return """📝 *Formulir Pendaftaran EcoBot*
─────────────────────────────────

Silakan isi informasi berikut:

*Format:*
```
Nama: (nama lengkap Anda)
Alamat: (alamat lengkap Anda)
```

*Contoh:*
```
Nama: Budi Santoso
Alamat: Jl. Merdeka No. 123, RT 02 RW 05
```

Kirim informasi Anda sesuai format di atas."""

    @staticmethod
    def format_feature_list(title: str, features: list) -> str:
        """Format feature list"""
        header = f"🔧 {title}\n{'─' * 35}\n\n"
        feature_list = "\n".join([f"• {feature}" for feature in features])
        return header + feature_list

    @staticmethod
    def ensure_length_limit(message: str, max_length: int = 1000) -> str:
        """Ensure message doesn't exceed length limit"""
        if len(message) <= max_length:
            return message

        return message[: max_length - 3] + "..."

    @staticmethod
    def format_list(items: list, bullet: str = "•") -> str:
        """Format list items"""
        return "\n".join([f"{bullet} {item}" for item in items])


class ValidationUtils:
    """Validation utilities"""

    @staticmethod
    def validate_registration_info(message: str) -> Optional[Dict[str, str]]:
        """Parse and validate registration information"""
        lines = message.strip().split("\n")

        name = None
        address = None

        for line in lines:
            line = line.strip()
            if line.lower().startswith("nama:"):
                name = line.split(":", 1)[1].strip()
            elif line.lower().startswith("alamat:"):
                address = line.split(":", 1)[1].strip()

        # Validate parsed info
        if not name or not address:
            return None

        if len(name) < 2 or len(address) < 5:
            return None

        return {"name": name, "address": address}

    @staticmethod
    def validate_image_format(content_type: str) -> bool:
        """Validate image content type"""
        from core.constants import SUPPORTED_IMAGE_FORMATS

        return content_type.lower() in SUPPORTED_IMAGE_FORMATS


class LoggerUtils:
    """Logging utilities"""

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get configured logger"""
        logger = logging.getLogger(name)
        return logger

    @staticmethod
    def log_error(logger: logging.Logger, error: Exception, context: str = None):
        """Log error with context"""
        message = f"Error in {context}: {str(error)}" if context else str(error)
        logger.error(message, exc_info=True)

    @staticmethod
    def log_request(logger: logging.Logger, endpoint: str, data: Dict[str, Any] = None):
        """Log API request"""
        message = f"API Request to {endpoint}"
        if data:
            message += f" with data: {data}"
        logger.info(message)
