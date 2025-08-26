"""
Registration Service
Handles user registration process
"""

from typing import Dict, Any, Optional
from core.utils import LoggerUtils, ValidationUtils, MessageFormatter
from core.config import get_config
from core.constants import REGISTRATION_STATUS, ICONS
from database.models import UserModel


class RegistrationService:
    """Handle user registration process"""

    def __init__(self, user_model: UserModel):
        self.user_model = user_model
        self.logger = LoggerUtils.get_logger(__name__)
        self.pending_registrations = {}
        self.config = get_config()

    def is_registration_required(self, phone_number: str) -> bool:
        """Check if user needs to register - always False (auto-registration enabled)"""
        try:
            mode = self.config.get_app_config().registration_mode
            return mode == "manual"
        except Exception:
            return False

    def handle_registration_command(
        self, phone_number: str, message: str
    ) -> Dict[str, Any]:
        """Handle registration-related commands depending on mode"""
        if not self.is_registration_required(phone_number):
            return {
                "status": "registration_disabled",
                "message": "Pendaftaran otomatis aktif. Anda dapat langsung menggunakan bot tanpa perlu mendaftar manual.",
            }
        # Manual mode: start or process registration
        if phone_number not in self.pending_registrations:
            return self._start_registration(phone_number)
        else:
            return self._process_registration_info(phone_number, message)

    def _start_registration(self, phone_number: str) -> Dict[str, Any]:
        """Start registration process"""
        try:
            self.user_model.create_pending_user(phone_number)

            self.pending_registrations[phone_number] = {
                "step": "waiting_info",
                "data": {},
            }

            response = self._generate_registration_prompt()

            return {"status": "registration_started", "message": response}

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "starting registration")
            return {
                "status": "registration_error",
                "message": "Maaf, terjadi kesalahan saat memulai pendaftaran. Silakan coba lagi.",
            }

    def _process_registration_info(
        self, phone_number: str, message: str
    ) -> Dict[str, Any]:
        """Process registration information from user"""
        try:
            parsed_info = ValidationUtils.validate_registration_info(message)

            if not parsed_info:
                return {
                    "status": "invalid_format",
                    "message": self._generate_format_error_message(),
                }

            success = self.user_model.complete_user_registration(
                phone_number, parsed_info["name"], parsed_info["address"]
            )

            if success:
                if phone_number in self.pending_registrations:
                    del self.pending_registrations[phone_number]

                return {
                    "status": "registration_success",
                    "message": self._generate_success_message(parsed_info["name"]),
                }
            else:
                return {
                    "status": "registration_failed",
                    "message": "Mohon maaf, pendaftaran Anda gagal. Terjadi kesalahan sistem. Silakan coba lagi atau hubungi admin.",
                }

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "processing registration")
            return {
                "status": "registration_error",
                "message": "Terjadi kesalahan saat memproses pendaftaran. Silakan coba lagi.",
            }

    def _generate_registration_prompt(self) -> str:
        """Generate registration prompt message"""
        return MessageFormatter.format_registration_form()

    def _generate_format_error_message(self) -> str:
        """Generate format error message"""
        response = MessageFormatter.format_info_header("Data Belum Lengkap")
        response += (
            "Kirimkan nama dan alamat Anda dalam format bebas.\n\n"
            "Contoh:\n"
            "• nama saya jhon, alamat jalan merdeka\n"
            "• Jhon — Jl. Merdeka 12\n\n"
            "Sistem akan merapikan data secara otomatis."
        )

        return response

    def _generate_success_message(self, name: str) -> str:
        """Generate registration success message"""
        response = MessageFormatter.format_success_header(f"Selamat Datang, {name}!")
        response += (
            "🎉 Anda berhasil terdaftar sebagai pengguna EcoBot .\n\n"
        )

        features = [
            "🎓 *Edukasi* - Tips pengelolaan sampah ramah lingkungan",
            "📅 *Jadwal* - Jadwal pengumpulan sampah terbaru",
            "📍 *Lokasi* - Titik pengumpulan sampah terdekat",
            "🏆 *Point* - Sistem reward (segera hadir)",
        ]
        response += MessageFormatter.format_feature_list(
            "Fitur yang Tersedia", features
        )

        response += "\n\n💡 *Cara Penggunaan:*\n"
        response += "• 📸 Kirim foto sampah untuk identifikasi otomatis\n"
        response += '• 💬 Ketik nama fitur (contoh: "edukasi", "lokasi")\n'
        response += "• ❓ Tanya langsung tentang pengelolaan sampah\n\n"
        response += (
            "🌱 *Selamat bergabung dalam program pengelolaan sampah ramah lingkungan!*"
        )

        return response

    def get_unregistered_user_message(self) -> str:
        """Get message for unregistered users - auto-registration enabled"""
        return (
            "🎉 Selamat datang di EcoBot!\n\n"
            "✅ Pendaftaran otomatis telah diaktifkan\n"
            "📱 Anda dapat langsung menggunakan semua fitur bot\n\n"
            "Ketik 'bantuan' untuk melihat fitur yang tersedia."
        )
