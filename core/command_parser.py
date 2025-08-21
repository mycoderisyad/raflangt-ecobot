"""
Command Parser
Handles parsing and validation of user commands
"""

from typing import Dict, Any
from core.constants import COMMAND_MAPPING, FEATURE_STATUS


class CommandParser:
    """Command parsing functionality"""
    
    def parse_command(self, message: str, phone_number: str = None) -> Dict[str, Any]:
        """Parse command from message"""
        if not message:
            return {'status': 'not_command', 'command': None, 'args': None}
        
        message_lower = message.lower().strip()
        
        # Check for commands (with or without /)
        command_text = message_lower[1:] if message_lower.startswith('/') else message_lower
        parts = command_text.split(' ', 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        # Find matching command
        for cmd_key, cmd_info in COMMAND_MAPPING.items():
            if command in cmd_info['aliases']:
                # Check feature access for user role
                user_role = self._get_user_role(phone_number) if phone_number else 'warga'
                
                if cmd_info['feature'] in FEATURE_STATUS.get(user_role, {}):
                    if FEATURE_STATUS[user_role][cmd_info['feature']]:
                        return {
                            'status': 'available',
                            'command': cmd_key,
                            'args': args,
                            'handler': cmd_info['handler'],
                            'feature': cmd_info['feature'],
                            'description': cmd_info['description']
                        }
                    else:
                        return {
                            'status': 'coming_soon',
                            'command': cmd_key,
                            'args': args,
                            'feature': cmd_info['feature'],
                            'description': cmd_info['description']
                        }
                else:
                    return {
                        'status': 'no_permission',
                        'command': cmd_key,
                        'args': args,
                        'feature': cmd_info['feature'],
                        'description': cmd_info['description']
                    }
        
        return {
            'status': 'unknown_command',
            'command': command,
            'args': args
        }
    
    def _get_user_role(self, phone_number: str) -> str:
        """Get user role from database"""
        from core.role_manager import RoleManager
        return RoleManager.get_user_role(phone_number)
