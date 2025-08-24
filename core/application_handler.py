"""
Main Application Handler
Clean microservice-based message processing
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from core.config import get_config
from core.utils import LoggerUtils
from core.constants import USER_ROLES, COMMAND_MAPPING, FEATURE_STATUS
from core.role_manager import RoleManager
from core.command_parser import CommandParser
from core.admin_handler import AdminCommandHandler
from services.whatsapp_service import WhatsAppService

from services.message_service import MessageService
from services.registration_service import RegistrationService
from database.models import UserModel
from core.database_manager import get_database_manager


class ApplicationHandler:
    """Main application handler for processing messages"""

    def __init__(self):
        self.config = get_config()
        self.logger = LoggerUtils.get_logger(__name__)

        # Initialize services
        self.whatsapp_service = WhatsAppService()
        self.message_service = MessageService()

        # Initialize database and user management
        self.db_manager = get_database_manager()
        self.user_model = UserModel(self.db_manager)
        self.role_manager = RoleManager()
        self.command_parser = CommandParser()
        self.admin_handler = AdminCommandHandler(
            self.whatsapp_service, self.message_service
        )
        self.registration_service = RegistrationService(self.user_model)
        self.report_service = None  # Will be initialized when needed

        self.logger.info("Application handler initialized successfully")

    def handle_incoming_message(self, request) -> Dict[str, Any]:
        """Process incoming WhatsApp message"""
        try:
            webhook_data = request.get_json()
            if not webhook_data:
                return {"status": "error", "message": "No data received"}

            # Parse message data
            message_data = self.whatsapp_service.parse_webhook_message(webhook_data)
            if not message_data:
                return {"status": "ignored", "message": "Not a message event"}

            # Route message based on type
            if message_data["message_type"] == "image":
                reply = self._handle_image_message(
                    message_data["media_url"],
                    message_data.get("media_info", {}),
                    message_data["from_number"],
                )
                self.user_model.increment_user_stats(
                    message_data["from_number"], "image"
                )
            elif (
                message_data["message_type"] == "text" and message_data["message_body"]
            ):
                reply = self._handle_text_message(
                    message_data["message_body"], message_data["from_number"]
                )
                self.user_model.increment_user_stats(
                    message_data["from_number"], "message"
                )
            else:
                reply = self._get_help_message(message_data["from_number"])

            # Send reply
            success = self.whatsapp_service.send_message(
                message_data["from_number"], reply
            )

            return {
                "status": "success" if success else "partial_success",
                "message": "Message processed",
            }

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "handling incoming message")
            return {"status": "error", "message": str(e)}

    def _handle_image_message(self, media_url: str, media_info: Dict[str, Any], phone_number: str) -> str:
        """Handle image message with AI Agent analysis"""
        try:
            # Auto-create user if not exists (no manual registration required)
            from core.utils import normalize_phone_for_db
            normalized_phone = normalize_phone_for_db(phone_number)
            self.user_model.create_or_update_user(normalized_phone)

            # Download image
            image_data = self.whatsapp_service.download_media(media_url, media_info)
            if not image_data:
                return self.message_service.format_error_response("general_error")

            # Use AI Agent for image analysis (includes personalization and memory)
            from services.ai_agent import AIAgent
            ai_agent = AIAgent()
            
            # Process image with AI Agent
            ai_result = ai_agent.process_image_message(image_data, normalized_phone, 'hybrid')
            
            if ai_result and ai_result.get("status") == "success":
                # Save classification to database if available
                try:
                    from database.models import WasteClassificationModel
                    
                    analysis_result = ai_result.get("analysis_result", {})
                    if analysis_result.get("waste_type"):
                        waste_model = WasteClassificationModel(self.db_manager)
                        waste_model.save_classification(
                            normalized_phone,
                            analysis_result["waste_type"],
                            analysis_result["confidence"],
                            analysis_result.get("method", "ai_agent"),
                        )
                except Exception as e:
                    LoggerUtils.log_error(self.logger, e, "saving classification")
                
                return ai_result.get("reply_sent", "Analisis gambar berhasil")

            # Fallback response if AI Agent fails
            return """Maaf, ada kendala saat menganalisis gambar.

Silakan coba lagi dalam beberapa saat atau hubungi admin untuk bantuan."""

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "handling image message")
            return self.message_service.format_error_response("general_error")

    def _handle_text_message(self, message_body: str, phone_number: str) -> str:
        """Handle text message with AI-first approach"""
        try:
            # Auto-create user if not exists (no manual registration required)
            from core.utils import normalize_phone_for_db
            normalized_phone = normalize_phone_for_db(phone_number)
            self.user_model.create_or_update_user(normalized_phone)

            # Check for admin commands
            admin_command = self.admin_handler.parse_admin_command(message_body)
            if admin_command:
                admin_result = self.admin_handler.handle_admin_command(
                    admin_command["command"], admin_command["args"], phone_number
                )
                return admin_result.get("message", "Admin command executed")

            # Use AI Agent for natural conversation (primary approach)
            from services.ai_agent import AIAgent
            ai_agent = AIAgent()
            
            # Process message with AI Agent (includes long-term memory)
            ai_result = ai_agent.process_message(message_body, normalized_phone, 'hybrid')
            
            if ai_result and ai_result.get("status") == "success":
                return ai_result.get("reply_sent", "Maaf, ada kesalahan dalam pemrosesan pesan.")

            # Fallback to command parsing only if AI fails
            command_info = self.command_parser.parse_command(message_body, phone_number)
            user_role = self.role_manager.get_user_role(normalized_phone)

            if command_info["status"] == "no_permission":
                return self.message_service.format_error_response(
                    "no_permission", user_role
                )
            elif command_info["status"] == "coming_soon":
                return self.message_service.format_error_response("coming_soon")
            elif command_info["status"] == "available":
                            return self._route_command_fallback(
                command_info, normalized_phone, user_role
            )
            else:
                # Ultimate fallback
                return self._get_help_message(normalized_phone)

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "handling text message")
            return self.message_service.format_error_response("general_error")

    def _route_command_fallback(
        self, command_info: Dict[str, Any], phone_number: str, user_role: str
    ) -> str:
        """Fallback command routing when AI fails"""
        handler = command_info["handler"]
        args = command_info["args"]

        # For critical commands, use direct AI queries with specific context
        if handler in ["help"]:
            return self._get_help_message(phone_number)
        elif handler == "report":
            return self._handle_report_request(normalized_phone, user_role)
        elif handler in ["schedule", "location", "points", "statistics"]:
            # Try AI response with specific context
            context_message = f"User asking about {handler}: {args or ''}"
            # Use AI Agent instead of legacy ai_service
            from services.ai_agent import AIAgent
            ai_agent = AIAgent()
            ai_result = ai_agent.process_message(context_message, normalized_phone, 'hybrid')
            if ai_result and ai_result.get("status") == "success":
                return ai_result.get("reply_sent", "Maaf, ada kesalahan dalam pemrosesan pesan.")

        # Ultimate fallback for unsupported features
        return """🤖 Maaf, fitur ini sedang dalam pengembangan. 

Saat ini saya bisa membantu:
📸 Identifikasi sampah dari foto
Jawab pertanyaan tentang pengelolaan sampah
Info lokasi dan jadwal pengumpulan
🎓 Tips dan edukasi lingkungan

Coba tanyakan hal lain atau kirim foto sampah ya! 🌱"""

    def _handle_general_conversation(
        self, message: str, phone_number: str = None
    ) -> str:
        """Handle general conversation using AI Agent"""
        # Use AI Agent instead of legacy ai_service
        from services.ai_agent import AIAgent
        ai_agent = AIAgent()
        ai_result = ai_agent.process_message(message, phone_number, 'hybrid')
        if ai_result and ai_result.get("status") == "success":
            return ai_result.get("reply_sent", "Maaf, ada kesalahan dalam pemrosesan pesan.")

        # Fallback response
        return """🤖 Halo! Saya EcoBot, asisten pengelolaan sampah untuk desa kita.

📸 Kirim foto sampah untuk identifikasi
Tanyakan tentang: edukasi, jadwal, lokasi
Ketik 'help' untuk melihat semua fitur

Apa yang bisa saya bantu hari ini? 🌱"""

    def _handle_schedule_request(self) -> str:
        """Handle schedule request"""
        # Mock schedule data
        schedule_data = {
            "Senin": "Sampah Organik - 07:00-09:00",
            "Rabu": "Sampah Anorganik - 07:00-09:00",
            "Jumat": "Sampah B3 - 08:00-10:00",
        }
        return self.message_service.format_schedule_response(schedule_data)

    def _handle_location_request(self) -> str:
        """Handle location request"""
        maps_data = self.message_service.get_maps_data()
        return self.message_service.format_location_response(maps_data)

    def _handle_points_request(self, phone_number: str) -> str:
        """Handle points request"""
        return self.message_service.format_error_response("coming_soon")

    def _handle_redeem_request(self) -> str:
        """Handle redeem request"""
        return self.message_service.format_error_response("coming_soon")

    def _handle_statistics_request(self, user_role: str) -> str:
        """Handle statistics request"""
        # Mock statistics
        stats = {
            "active_users": 45,
            "images_processed": 123,
            "successful_classifications": 118,
            "total_users": 67,
            "organic_count": 78,
            "inorganic_count": 45,
            "b3_count": 12,
            "system_status": "Normal",
            "uptime": "99.8%",
        }
        return self.message_service.format_statistics_response(stats, user_role)

    def _handle_report_request(self, phone_number: str, user_role: str) -> str:
        """Handle report request"""
        if user_role == "warga":
            return self.message_service.format_report_response(user_role)

        # For coordinators and admins, generate and send email report
        try:
            # Import ReportService when needed to avoid circular import
            if self.report_service is None:
                from services.report_service import ReportService
                self.report_service = ReportService(self.whatsapp_service)
            
            # Use ReportService for report generation
            result = self.report_service.generate_and_send_report_async(
                phone_number, user_role
            )

            if result["success"]:
                return result["message"]
            else:
                return result["message"]

        except Exception as e:
            return f"Error: {str(e)}"



    def _get_help_message(self, phone_number: str) -> str:
        """Generate comprehensive help message"""
        user_role = self.role_manager.get_user_role(phone_number)

        response = """🤖 EcoBot - Menu Lengkap
Halo warga Desa Cukangkawung! Berikut fitur yang tersedia:

📚 Fitur Utama (Semua Pengguna):
• edukasi - Tips & panduan pengelolaan sampah
• jadwal - Jadwal pengumpulan sampah
• lokasi - Titik pengumpulan + peta Google Maps
• 📸 Kirim foto sampah untuk identifikasi AI

💡 Contoh Pertanyaan Edukasi:
• "apa itu kompos?"
• "bagaimana cara memilah?"
• "manfaat daur ulang"
• "sampah organik"

Fitur Poin (Coming Soon):
• daftar - Daftar sistem poin
• point - Cek poin reward
• redeem - Tukar poin dengan hadiah"""

        # Add role-specific features
        if user_role in ["koordinator", "admin"]:
            response += """

👥 Fitur Koordinator:
• statistik - Data pengguna & aktivitas
• laporan - Generate laporan email"""

        response += """

Cara Pakai:
• Ketik nama fitur langsung (tanpa /)
• Kirim foto sampah untuk analisis
• Tanya apa saja tentang sampah!

Mari bersama jaga lingkungan desa kita!"""

        return response

    def _get_waste_education(self, waste_type: str) -> Dict[str, Any]:
        """Get education content for waste type"""
        education_data = self.message_service.get_education_messages()
        return education_data.get(waste_type.lower(), education_data.get("general", {}))
