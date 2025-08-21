"""
Message Service
Handles message loading and formatting
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from core.utils import LoggerUtils, MessageFormatter
from core.constants import ICONS


class MessageService:
    """Message service for loading and formatting"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
        self.messages = self._load_messages()
    
    def _load_messages(self) -> Dict[str, Any]:
        """Load messages from JSON files"""
        messages = {}
        messages_dir = Path('messages')
        
        if not messages_dir.exists():
            self.logger.warning("Messages directory not found")
            return {}
        
        # Load all JSON files from messages directory
        for json_file in messages_dir.glob('.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    messages[json_file.stem] = file_data
                    self.logger.info(f"Loaded messages from {json_file.name}")
            except Exception as e:
                LoggerUtils.log_error(self.logger, e, f"loading {json_file.name}")
        
        return messages
    
    def get_whatsapp_messages(self) -> Dict[str, Any]:
        """Get WhatsApp messages"""
        return self.messages.get('whatsapp_messages', {})
    
    def get_education_messages(self) -> Dict[str, Any]:
        """Get education messages"""
        return self.messages.get('education_messages', {})
    
    def get_email_templates(self) -> Dict[str, Any]:
        """Get email templates"""
        return self.messages.get('email_templates', {})
    
    def get_maps_data(self) -> Dict[str, Any]:
        """Get maps data"""
        return self.messages.get('maps_data', {})
    
    def format_error_response(self, error_type: str, user_role: str = 'warga') -> str:
        """Format error response"""
        error_messages = {
            'no_permission': "Maaf, Anda tidak memiliki izin untuk mengakses fitur ini.\n\nSilakan hubungi admin untuk informasi lebih lanjut.",
            'feature_disabled': "Fitur ini sedang dalam maintenance.\n\nSilakan coba lagi nanti.",
            'coming_soon': "Fitur ini akan segera hadir.\n\nTerima kasih atas kesabaran Anda.",
            'invalid_command': "Perintah tidak dikenali.\n\nSilakan ketik 'help' untuk melihat daftar perintah.",
            'general_error': "Terjadi kesalahan sistem.\n\nSilakan coba lagi atau hubungi admin jika masalah berlanjut.",
            'registration_required': "Anda perlu mendaftar terlebih dahulu untuk menggunakan layanan ini."
        }
        
        message = error_messages.get(error_type, error_messages['general_error'])
        return MessageFormatter.format_header("Error", ICONS['ERROR']) + message
    
    def format_success_response(self, message: str) -> str:
        """Format success response"""
        return MessageFormatter.format_header("Success", ICONS['SUCCESS']) + message
    
    def format_education_response(self, content: Dict[str, Any]) -> str:
        """Format education response"""
        if not content:
            return self.format_error_response('general_error')
        
        response = MessageFormatter.format_header("Tips Edukasi", ICONS['EDUCATION'])
        
        if 'tips' in content:
            response += "Tips Pengelolaan Sampah:\n"
            response += MessageFormatter.format_list(content['tips'])
            response += "\n\n"
        
        if 'additional_info' in content:
            response += "Informasi Tambahan:\n"
            response += content['additional_info']
        
        return MessageFormatter.ensure_length_limit(response)
    
    def format_schedule_response(self, schedule_data: Dict[str, Any]) -> str:
        """Format schedule response"""
        response = MessageFormatter.format_header("Jadwal Pengumpulan", ICONS['SCHEDULE'])
        
        if not schedule_data:
            response += "Jadwal pengumpulan sampah akan diumumkan segera."
        else:
            response += "Jadwal pengumpulan sampah:\n"
            for day, info in schedule_data.items():
                response += f"• {day}: {info}\n"
        
        return MessageFormatter.ensure_length_limit(response)
    
    def format_location_response(self, location_data: Dict[str, Any]) -> str:
        """Format location response"""
        response = MessageFormatter.format_header("Lokasi Pengumpulan", ICONS['LOCATION'])
        
        if not location_data:
            response += "Data lokasi pengumpulan tidak tersedia."
        else:
            response += "Titik pengumpulan sampah terdekat:\n\n"
            for location in location_data.get('locations', []):
                response += f"• {location.get('name', 'Unknown')}\n"
                response += f"  Alamat: {location.get('address', 'N/A')}\n"
                response += f"  Jenis: {location.get('type', 'N/A')}\n\n"
        
        return MessageFormatter.ensure_length_limit(response)
    
    def format_statistics_response(self, stats: Dict[str, Any], user_role: str) -> str:
        """Format statistics response"""
        response = MessageFormatter.format_header("Statistik EcoBot", ICONS['STATISTICS'])
        
        if user_role == 'warga':
            return response + "Fitur statistik hanya tersedia untuk Koordinator dan Admin.\n\nSilakan hubungi koordinator desa untuk informasi lebih lanjut."
        
        response += "Data Hari Ini:\n"
        response += f"• Pengguna Aktif: {stats.get('active_users', 0)}\n"
        response += f"• Foto Dianalisis: {stats.get('images_processed', 0)}\n"
        response += f"• Klasifikasi Berhasil: {stats.get('successful_classifications', 0)}\n\n"
        
        response += "Data Minggu Ini:\n"
        response += f"• Total Pengguna: {stats.get('total_users', 0)}\n"
        response += f"• Sampah Organik: {stats.get('organic_count', 0)}\n"
        response += f"• Sampah Anorganik: {stats.get('inorganic_count', 0)}\n"
        response += f"• Sampah B3: {stats.get('b3_count', 0)}\n\n"
        
        if user_role == 'admin':
            response += "Sistem:\n"
            response += f"• Status: {stats.get('system_status', 'Normal')}\n"
            response += f"• Uptime: {stats.get('uptime', '99.9%')}\n"
        
        return MessageFormatter.ensure_length_limit(response)
    
    def format_report_response(self, user_role: str) -> str:
        """Format report response"""
        response = MessageFormatter.format_header("Laporan EcoBot", ICONS['REPORT'])
        
        if user_role == 'warga':
            return response + "Fitur laporan hanya tersedia untuk Koordinator dan Admin.\n\nSilakan hubungi koordinator desa untuk informasi lebih lanjut."
        
        response += "Laporan sedang diproses...\n\n"
        response += "Laporan akan dikirim ke email Anda dalam beberapa menit.\n\n"
        response += "Isi Laporan:\n"
        response += "• Statistik penggunaan\n"
        response += "• Data klasifikasi sampah\n"
        response += "• Analisis pengguna\n"
        response += "• Rekomendasi\n\n"
        response += "Periksa email Anda dalam 5-10 menit."
        
        return response
