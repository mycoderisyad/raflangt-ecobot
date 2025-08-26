"""
Utility functions for EcoBot
"""

import re
import logging
from typing import Optional, Dict, Any


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to standard format
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Normalized phone number
    """
    if not phone:
        return phone
    
    # Remove common suffixes
    phone = phone.replace("@c.us", "").replace("@s.whatsapp.net", "")
    
    # Remove non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Ensure proper format
    if phone.startswith("+62"):
        return phone
    elif phone.startswith("62"):
        return "+" + phone
    elif phone.startswith("0"):
        return "+62" + phone[1:]
    else:
        return phone


def normalize_phone_for_db(phone: str) -> str:
    """
    Normalize phone number for database storage (add @c.us suffix)
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Phone number with @c.us suffix for database
    """
    # Remove common suffixes first
    clean_phone = phone.replace("@c.us", "").replace("@s.whatsapp.net", "")
    
    # Remove non-digit characters except +
    clean_phone = re.sub(r'[^\d+]', '', clean_phone)
    
    # Ensure proper format without + prefix for database
    if clean_phone.startswith("+62"):
        clean_phone = clean_phone[1:]  # Remove + for database storage
    elif clean_phone.startswith("62"):
        clean_phone = clean_phone  # Keep as is
    elif clean_phone.startswith("0"):
        clean_phone = "62" + clean_phone[1:]  # Convert 08 to 62
    
    # Add @c.us suffix
    if clean_phone and not clean_phone.endswith("@c.us"):
        return clean_phone + "@c.us"
    return clean_phone


def normalize_phone_for_display(phone: str) -> str:
    """
    Normalize phone number for display (remove @c.us suffix)
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Clean phone number for display
    """
    return normalize_phone_number(phone)


def is_valid_phone_number(phone: str) -> bool:
    """
    Check if phone number is valid
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Remove suffixes for validation
    clean_phone = normalize_phone_number(phone)
    
    # Check Indonesian format
    if clean_phone.startswith("+62"):
        # Should be +62 + 8-11 digits
        digits = clean_phone[3:]
        return len(digits) >= 8 and len(digits) <= 11 and digits.isdigit()
    
    return False


def extract_phone_from_whatsapp_id(whatsapp_id: str) -> str:
    """
    Extract clean phone number from WhatsApp ID
    
    Args:
        whatsapp_id: WhatsApp ID (e.g., "6285156084435@c.us")
        
    Returns:
        Clean phone number
    """
    return normalize_phone_number(whatsapp_id)


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
        return (
            "Pendaftaran EcoBot\n"
            "Silakan kirim nama dan alamat Anda (format bebas).\n"
            "Contoh: 'nama saya jhon, alamat jalan merdeka' atau 'Jhon — Jl. Merdeka 12'.\n"
        )
    
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
        text = message.strip()
        if not text:
            return None

        lowered = text.lower()

        # Try keyword-based extraction (format bebas)
        name = None
        address = None

        name_match = re.search(r"nama\s*[:\-]?\s*(.+?)(?:,|\n|$)", lowered, re.IGNORECASE)
        if name_match:
            name = text[name_match.start(1):name_match.end(1)].strip()

        addr_match = re.search(r"alamat\s*[:\-]?\s*(.+)$", lowered, re.IGNORECASE | re.MULTILINE)
        if addr_match:
            address = text[addr_match.start(1):addr_match.end(1)].strip()

        # If keywords not found, fallback heuristics: two lines or two chunks separated by comma/dash
        if not name or not address:
            # newline split
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            if len(parts) >= 2 and (not name or not address):
                if not name:
                    name = parts[0]
                if not address:
                    address = parts[1]

        if (not name or not address) and "," in text:
            comma_parts = [p.strip() for p in text.split(",") if p.strip()]
            if len(comma_parts) >= 2:
                if not name:
                    name = comma_parts[0]
                if not address:
                    address = ", ".join(comma_parts[1:]).strip()

        # Final minimal validation; AI Agent will further normalize
        if not name or not address:
            return None
        if len(name) < 2 or len(address) < 3:
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
