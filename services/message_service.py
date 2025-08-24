"""
Message Service
Handles message loading and formatting
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from core.utils import LoggerUtils, MessageFormatter
from core.constants import ICONS
from core.response_formatter import ResponseFormatter


class MessageService:
    """Message service for loading and formatting"""

    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
        self.messages = self._load_messages()

    def _load_messages(self) -> Dict[str, Any]:
        """Load messages from JSON files"""
        messages = {}
        messages_dir = Path("messages")

        if not messages_dir.exists():
            self.logger.warning("Messages directory not found")
            return {}

        # Load all JSON files from messages directory
        for json_file in messages_dir.glob(".json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    messages[json_file.stem] = file_data
                    self.logger.info(f"Loaded messages from {json_file.name}")
            except Exception as e:
                LoggerUtils.log_error(self.logger, e, f"loading {json_file.name}")

        return messages

    def get_whatsapp_messages(self) -> Dict[str, Any]:
        """Get WhatsApp messages"""
        return self.messages.get("whatsapp_messages", {})

    def get_education_messages(self) -> Dict[str, Any]:
        """Get education messages"""
        return self.messages.get("education_messages", {})

    def get_email_templates(self) -> Dict[str, Any]:
        """Get email templates"""
        return self.messages.get("email_templates", {})

    def get_maps_data(self) -> Dict[str, Any]:
        """Get maps data"""
        return self.messages.get("maps_data", {})

    def format_error_response(self, error_type: str, user_role: str = "warga") -> str:
        """Format error response"""
        return ResponseFormatter.format_error_response(error_type, user_role)

    def format_success_response(self, message: str) -> str:
        """Format success response"""
        return ResponseFormatter.format_success_response(message)

    def format_education_response(self, content: Dict[str, Any]) -> str:
        """Format education response"""
        return ResponseFormatter.format_education_response(content)

    def format_schedule_response(self, schedule_data: Dict[str, Any]) -> str:
        """Format schedule response"""
        return ResponseFormatter.format_schedule_response(schedule_data)

    def format_location_response(self, location_data: Dict[str, Any]) -> str:
        """Format location response"""
        return ResponseFormatter.format_location_response(location_data)

    def format_statistics_response(self, stats: Dict[str, Any], user_role: str) -> str:
        """Format statistics response"""
        return ResponseFormatter.format_statistics_response(stats, user_role)

    def format_report_response(self, user_role: str) -> str:
        """Format report response"""
        return ResponseFormatter.format_report_response(user_role)
