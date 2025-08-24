"""
Command Parser for EcoBot
Handles various commands and routes them to appropriate handlers
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from core.constants import COMMAND_MAPPING, USER_ROLES, FEATURE_STATUS

logger = logging.getLogger(__name__)


class CommandParser:
    """Parse and route user commands"""

    def __init__(self):
        self.command_mapping = COMMAND_MAPPING
        self.user_roles = USER_ROLES
        self.feature_status = FEATURE_STATUS

    def parse_command(self, message: str, user_role: str = "warga") -> Dict[str, Any]:
        """
        Parse user message and extract command information
        
        Args:
            message: User message text
            user_role: User's role in the system
            
        Returns:
            Dict containing command information
        """
        message = message.strip()
        
        # Check for AI mode switching commands first
        ai_mode_commands = {
            "/layanan-ecobot": "ecobot",
            "/general-ecobot": "general", 
            "/hybrid-ecobot": "hybrid"
        }
        
        for command, mode in ai_mode_commands.items():
            if message.lower().startswith(command.lower()):
                return {
                    "type": "ai_mode_switch",
                    "command": command,
                    "mode": mode,
                    "description": f"Switch AI Agent to {mode} mode",
                    "handler": "ai_mode_switch",
                    "feature": "ai_agent"
                }
        
        # Check for help command
        if message.lower().startswith("/help") or message.lower().startswith("/bantuan"):
            return {
                "type": "help",
                "command": "help",
                "description": "Show available commands and features",
                "handler": "help",
                "feature": "edukasi"
            }
        
        # Check for other commands
        for command_key, command_info in self.command_mapping.items():
            if self._matches_command(message, command_info["aliases"]):
                # Check if user has access to this feature
                if self._can_access_feature(user_role, command_info["feature"]):
                    return {
                        "type": "feature",
                        "command": command_key,
                        "description": command_info["description"],
                        "handler": command_info["handler"],
                        "feature": command_info["feature"],
                        "aliases": command_info["aliases"]
                    }
                else:
                    return {
                        "type": "access_denied",
                        "command": command_key,
                        "description": f"Fitur {command_info['description']} tidak tersedia untuk role {user_role}",
                        "handler": "access_denied",
                        "feature": command_info["feature"]
                    }
        
        # No command found
        return {
            "type": "no_command",
            "command": None,
            "description": "Pesan tidak dikenali sebagai command",
            "handler": "natural_language",
            "feature": "ai_agent"
        }

    def _matches_command(self, message: str, aliases: list) -> bool:
        """Check if message matches any command alias"""
        message_lower = message.lower()
        return any(alias.lower() in message_lower for alias in aliases)

    def _can_access_feature(self, user_role: str, feature: str) -> bool:
        """Check if user can access specific feature"""
        if user_role not in self.feature_status:
            return False
        
        return self.feature_status[user_role].get(feature, False)

    def get_available_commands(self, user_role: str = "warga") -> Dict[str, Any]:
        """Get available commands for user role"""
        available_commands = {}
        
        for command_key, command_info in self.command_mapping.items():
            if self._can_access_feature(user_role, command_info["feature"]):
                available_commands[command_key] = {
                    "description": command_info["description"],
                    "aliases": command_info["aliases"],
                    "feature": command_info["feature"]
                }
        
        # Add AI mode commands
        available_commands.update({
            "layanan-ecobot": {
                "description": "Switch AI Agent ke mode EcoBot Service (database only)",
                "aliases": ["/layanan-ecobot"],
                "feature": "ai_agent"
            },
            "general-ecobot": {
                "description": "Switch AI Agent ke mode General Waste Management",
                "aliases": ["/general-ecobot"],
                "feature": "ai_agent"
            },
            "hybrid-ecobot": {
                "description": "Switch AI Agent ke mode Hybrid (database + general)",
                "aliases": ["/hybrid-ecobot"],
                "feature": "ai_agent"
            }
        })
        
        return available_commands

    def get_command_help(self, user_role: str = "warga") -> str:
        """Generate help message for available commands"""
        available_commands = self.get_available_commands(user_role)
        
        help_text = f"🤖 **ECOBOB COMMANDS** 🤖\n\n"
        help_text += f"Role: {self.user_roles.get(user_role, {}).get('name', user_role)}\n\n"
        
        # AI Mode Commands
        help_text += "🔧 **AI AGENT MODES:**\n"
        help_text += "• `/layanan-ecobot` - Mode EcoBot Service (database only)\n"
        help_text += "• `/general-ecobot` - Mode General Waste Management\n"
        help_text += "• `/hybrid-ecobot` - Mode Hybrid (default)\n\n"
        
        # Feature Commands
        help_text += "📋 **FITUR UTAMA:**\n"
        for command_key, command_info in available_commands.items():
            if command_key not in ["layanan-ecobot", "general-ecobot", "hybrid-ecobot"]:
                aliases = ", ".join(command_info["aliases"][:3])  # Show first 3 aliases
                help_text += f"• `{aliases}` - {command_info['description']}\n"
        
        help_text += "\n💡 **TIPS:**\n"
        help_text += "• Gunakan command untuk fitur spesifik\n"
        help_text += "• Tanpa command = AI Agent natural conversation\n"
        help_text += "• `/help` untuk melihat command ini lagi\n"
        
        return help_text


# Initialize command parser
command_parser = CommandParser()


def get_command_parser():
    """Get the global command parser instance"""
    return command_parser
