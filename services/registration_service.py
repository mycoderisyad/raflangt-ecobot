"""
Registration Service
Handles user registration process
"""

from typing import Dict, Any, Optional
from core.utils import LoggerUtils, ValidationUtils, MessageFormatter
from core.constants import REGISTRATION_STATUS, ICONS
from database.models import UserModel


class RegistrationService:
    """Handle user registration process"""
    
    def __init__(self, user_model: UserModel):
        self.user_model = user_model
        self.logger = LoggerUtils.get_logger(__name__)
        self.pending_registrations = {}
    
    def is_registration_required(self, phone_number: str) -> bool:
        """Check if user needs to register"""
        status = self.user_model.get_user_registration_status(phone_number)
        return status in [REGISTRATION_STATUS['NEW'], REGISTRATION_STATUS['PENDING']]
    
    def handle_registration_command(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Handle registration-related commands"""
        message_lower = message.lower().strip()
        
        if message_lower == 'daftar':
            return self._start_registration(phone_number)
        
        if phone_number in self.pending_registrations:
            return self._process_registration_info(phone_number, message)
        
        return {
            'status': 'not_registration',
            'message': None
        }
    
    def _start_registration(self, phone_number: str) -> Dict[str, Any]:
        """Start registration process"""
        try:
            self.user_model.create_pending_user(phone_number)
            
            self.pending_registrations[phone_number] = {
                'step': 'waiting_info',
                'data': {}
            }
            
            response = self._generate_registration_prompt()
            
            return {
                'status': 'registration_started',
                'message': response
            }
            
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "starting registration")
            return {
                'status': 'registration_error',
                'message': "Maaf, terjadi kesalahan saat memulai pendaftaran. Silakan coba lagi."
            }
    
    def _process_registration_info(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Process registration information from user"""
        try:
            parsed_info = ValidationUtils.validate_registration_info(message)
            
            if not parsed_info:
                return {
                    'status': 'invalid_format',
                    'message': self._generate_format_error_message()
                }
            
            success = self.user_model.complete_user_registration(
                phone_number, 
                parsed_info['name'], 
                parsed_info['address']
            )
            
            if success:
                if phone_number in self.pending_registrations:
                    del self.pending_registrations[phone_number]
                
                return {
                    'status': 'registration_success',
                    'message': self._generate_success_message(parsed_info['name'])
                }
            else:
                return {
                    'status': 'registration_failed',
                    'message': "Mohon maaf, pendaftaran Anda gagal. Terjadi kesalahan sistem. Silakan coba lagi atau hubungi admin."
                }
                
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "processing registration")
            return {
                'status': 'registration_error',
                'message': "Terjadi kesalahan saat memproses pendaftaran. Silakan coba lagi."
            }
    
    def _generate_registration_prompt(self) -> str:
        """Generate registration prompt message"""
        response = MessageFormatter.format_header("Selamat datang di EcoBot!", ICONS['ROBOT'])
        response += "Silakan isi informasi di bawah ini untuk melanjutkan pendaftaran:\n\n"
        response += "Format:\n"
        response += "Nama: (nama lengkap Anda)\n"
        response += "Alamat: (alamat lengkap Anda)\n\n"
        response += "Contoh:\n"
        response += "Nama: Asep Surasep\n"
        response += "Alamat: Kampung Manggis RT 02 RW 05\n\n"
        response += "Kirim informasi Anda sesuai format di atas."
        
        return response
    
    def _generate_format_error_message(self) -> str:
        """Generate format error message"""
        response = MessageFormatter.format_header("Format tidak sesuai!", ICONS['ERROR'])
        response += "Silakan kirim informasi dengan format yang benar:\n\n"
        response += "Format:\n"
        response += "Nama: (nama lengkap Anda)\n"
        response += "Alamat: (alamat lengkap Anda)\n\n"
        response += "Contoh:\n"
        response += "Nama: Asep Surasep\n"
        response += "Alamat: Kampung Manggis RT 02 RW 05\n\n"
        response += "Pastikan Anda mengisi kedua informasi dengan lengkap."
        
        return response
    
    def _generate_success_message(self, name: str) -> str:
        """Generate registration success message"""
        response = MessageFormatter.format_header(f"Selamat {name}!", ICONS['SUCCESS'])
        response += "Anda sudah terdaftar sebagai pengguna EcoBot Desa Cukangkawung.\n\n"
        response += "Fitur yang Tersedia:\n"
        response += "• Edukasi - Tips pengelolaan sampah\n"
        response += "• Jadwal - Jadwal pengumpulan sampah\n"
        response += "• Lokasi - Titik pengumpulan terdekat\n"
        response += "• Point - Sistem reward (segera hadir)\n\n"
        response += "Cara Penggunaan:\n"
        response += "• Kirim foto sampah untuk identifikasi\n"
        response += "• Ketik nama fitur (contoh: \"edukasi\", \"lokasi\")\n"
        response += "• Tanya langsung tentang pengelolaan sampah\n\n"
        response += "Selamat bergabung dalam program pengelolaan sampah ramah lingkungan!"
        
        return response
    
    def get_unregistered_user_message(self) -> str:
        """Get message for unregistered users"""
        response = MessageFormatter.format_header("Halo! Selamat datang di EcoBot", ICONS['ROBOT'])
        response += "Anda belum terdaftar sebagai pengguna. Untuk menggunakan layanan EcoBot, silakan ketik:\n\n"
        response += "daftar\n\n"
        response += "untuk memulai proses pendaftaran.\n\n"
        response += "EcoBot adalah asisten AI untuk pengelolaan sampah di Desa Cukangkawung yang akan membantu Anda mengidentifikasi jenis sampah dan memberikan tips pengelolaan yang tepat."
        
        return response
