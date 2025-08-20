"""
Role and Permission Management
Mengelola peran pengguna dan izin akses fitur
"""

import logging
from typing import List, Dict, Any
from utils.constants import USER_ROLES, FEATURE_STATUS, COMMAND_MAPPING
from database.models import UserModel

logger = logging.getLogger(__name__)

class RoleManager:
    """Manage user roles and permissions"""
    
    def __init__(self, user_model: UserModel):
        self.user_model = user_model
    
    def get_user_role(self, phone_number: str) -> str:
        """Get user role"""
        return self.user_model.get_user_role(phone_number)
    
    def has_permission(self, phone_number: str, feature: str) -> bool:
        """Check if user has permission for a feature"""
        role = self.get_user_role(phone_number)
        role_config = USER_ROLES.get(role, USER_ROLES['warga'])
        
        # Admin has all permissions
        if 'all' in role_config['permissions']:
            return True
            
        # Check specific permissions
        permission_map = {
            'edukasi': 'view_education',
            'jadwal': 'view_schedule', 
            'lokasi': 'view_location',
            'point': 'view_points',
            'redeem': 'view_points',
            'statistik': 'view_statistics',
            'laporan': 'generate_reports'
        }
        
        required_permission = permission_map.get(feature)
        return required_permission in role_config['permissions']
    
    def is_feature_available(self, feature: str) -> bool:
        """Check if feature is available"""
        return FEATURE_STATUS.get(feature) == 'active'
    
    def get_available_features(self, phone_number: str) -> List[str]:
        """Get list of available features for user"""
        role = self.get_user_role(phone_number)
        role_config = USER_ROLES.get(role, USER_ROLES['warga'])
        
        if 'all' in role_config['features']:
            # Admin gets all active features
            return [f for f, status in FEATURE_STATUS.items() if status == 'active']
        
        # Filter features by role and availability
        available = []
        for feature in role_config['features']:
            if self.has_permission(phone_number, feature):
                available.append(feature)
                
        return available
    
    def get_role_info(self, phone_number: str) -> Dict[str, Any]:
        """Get complete role information for user"""
        role = self.get_user_role(phone_number)
        role_config = USER_ROLES.get(role, USER_ROLES['warga'])
        available_features = self.get_available_features(phone_number)
        
        return {
            'role': role,
            'role_name': role_config['name'],
            'permissions': role_config['permissions'],
            'available_features': available_features,
            'coming_soon_features': [f for f, status in FEATURE_STATUS.items() 
                                   if status == 'coming_soon' and f in role_config['features']]
        }

class CommandParser:
    """Parse and route commands based on user permissions"""
    
    def __init__(self, role_manager: RoleManager):
        self.role_manager = role_manager
    
    def parse_command(self, message: str, phone_number: str) -> Dict[str, Any]:
        """Parse message and determine command"""
        message_lower = message.lower().strip()
        
        # Check for each command type
        for command, keywords in COMMAND_MAPPING.items():
            if any(keyword in message_lower for keyword in keywords):
                # Check if user has permission
                if self.role_manager.has_permission(phone_number, command):
                    # Check if feature is available
                    if self.role_manager.is_feature_available(command):
                        return {
                            'command': command,
                            'status': 'available',
                            'message': message
                        }
                    else:
                        return {
                            'command': command,
                            'status': 'coming_soon',
                            'message': message
                        }
                else:
                    return {
                        'command': command,
                        'status': 'no_permission',
                        'message': message
                    }
        
        # No specific command found
        return {
            'command': 'general',
            'status': 'available',
            'message': message
        }
    
    def get_help_message(self, phone_number: str) -> str:
        """Generate help message based on user role"""
        role_info = self.role_manager.get_role_info(phone_number)
        
        message = f"*🤖 EcoBot - Panduan Penggunaan*\n\n"
        message += f"*Peran Anda:* {role_info['role_name']}\n\n"
        
        message += "*📋 Fitur yang Tersedia:*\n"
        
        feature_descriptions = {
            'edukasi': "💡 *Edukasi* - Tips pengelolaan sampah dan informasi lingkungan",
            'jadwal': "📅 *Jadwal* - Lihat jadwal pengumpulan sampah",
            'lokasi': "📍 *Lokasi* - Titik pengumpulan sampah terdekat dengan peta",
            'point': "⭐ *Point* - Lihat poin reward Anda",
            'redeem': "🎁 *Redeem* - Tukar poin dengan hadiah",
            'statistik': "📊 *Statistik* - Data layanan dan penggunaan",
            'laporan': "📧 *Laporan* - Kirim laporan melalui email"
        }
        
        for feature in role_info['available_features']:
            if feature in feature_descriptions:
                message += f"{feature_descriptions[feature]}\n"
        
        if role_info['coming_soon_features']:
            message += "\n*🔜 Segera Hadir:*\n"
            for feature in role_info['coming_soon_features']:
                if feature in feature_descriptions:
                    message += f"{feature_descriptions[feature]} _(coming soon)_\n"
        
        message += "\n*💬 Cara Penggunaan:*\n"
        message += "• Kirim foto sampah untuk identifikasi otomatis\n"
        message += "• Ketik nama fitur (contoh: 'edukasi', 'lokasi')\n"
        message += "• Tanya langsung tentang pengelolaan sampah\n"
        
        return message
