"""User registration service."""

import logging
from typing import Dict, Any

from src.config import get_settings
from src.database.models.user import UserModel

logger = logging.getLogger(__name__)


class RegistrationService:

    def __init__(self):
        self.user_model = UserModel()
        self.settings = get_settings()

    def is_manual_mode(self) -> bool:
        return self.settings.app.registration_mode == "manual"

    def register_user(self, phone: str, name: str, address: str) -> Dict[str, Any]:
        try:
            success = self.user_model.complete_registration(phone, name, address)
            if success:
                return {"status": "success", "message": f"Selamat datang, {name}! Registrasi berhasil."}
            return {"status": "error", "message": "Gagal menyimpan data registrasi."}
        except Exception as e:
            logger.error("Registration error: %s", e)
            return {"status": "error", "message": "Terjadi kesalahan saat registrasi."}
