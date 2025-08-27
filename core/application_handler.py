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
                    if analysis_result.get("waste_type") is not None:
                        waste_model = WasteClassificationModel(self.db_manager)
                        # Use keyword args to avoid positional mismatch
                        waste_model.save_classification(
                            user_phone=normalized_phone,
                            classification_result=analysis_result,
                            waste_type=analysis_result.get("waste_type"),
                            confidence=analysis_result.get("confidence"),
                            classification_method=analysis_result.get("method", "ai_agent"),
                            image_url=analysis_result.get("image_url"),
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

            # Handle AI mode switch commands BEFORE invoking the AI
            try:
                command_info = self.command_parser.parse_command(message_body) or {}
                if command_info.get("type") == "ai_mode_switch":
                    from services.ai_agent import AIAgent
                    ai_agent = AIAgent()
                    new_mode = command_info.get("mode", "hybrid")
                    switch_msg = ai_agent.switch_mode(normalized_phone, new_mode)
                    # Provide concise guidance after switching
                    if new_mode == "ecobot":
                        extra = (
                            "Mode database first aktif. Tanyakan lokasi/jadwal. \n\n"
                            "Untuk informasi lebih spesifik silakan gunakan /layanan-ecobot"
                        )
                    elif new_mode == "general":
                        extra = (
                            "Mode AI knowledge aktif. Untuk detail dari database gunakan /layanan-ecobot"
                        )
                    else:
                        extra = (
                            "Mode hybrid aktif. Data database akan diprioritaskan lalu AI sebagai fallback"
                        )
                    return f"{switch_msg}\n\n{extra}"
            except Exception:
                # If parsing fails, continue with AI handling
                pass

            # Use AI Agent for natural conversation (primary approach)
            from services.ai_agent import AIAgent
            ai_agent = AIAgent()
            
            # Process message with AI Agent (includes long-term memory)
            ai_result = ai_agent.process_message(message_body, normalized_phone, 'hybrid')
            
            # If AI produced any reply (success or graceful error), prefer returning it
            if ai_result and ai_result.get("reply_sent"):
                return ai_result.get("reply_sent", "Maaf, ada kesalahan dalam pemrosesan pesan.")

            # Fallback to command parsing only if AI fails
            user_role = self.role_manager.get_user_role(normalized_phone)
            command_info = self.command_parser.parse_command(message_body, user_role) or {}
            if "args" not in command_info:
                command_info["args"] = ""

            status = command_info.get("status")
            if status == "no_permission":
                return self.message_service.format_error_response(
                    "no_permission", user_role
                )
            elif status == "coming_soon":
                return self.message_service.format_error_response("coming_soon")
            elif status == "available":
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
        """Fallback command routing; try AI Agent first, then DB-backed handlers"""
        handler = command_info["handler"]
        args = command_info["args"]

        # For critical commands, use direct AI queries with specific context
        if handler in ["help"]:
            return self._get_help_message(phone_number)
        elif handler == "report":
            return self._handle_report_request(phone_number, user_role)
        elif handler in ["schedule", "location", "points", "statistics"]:
            # Try AI response with specific context
            context_message = f"User asking about {handler}: {args or ''}"
            # Use AI Agent instead of legacy ai_service
            from services.ai_agent import AIAgent
            ai_agent = AIAgent()
            ai_result = ai_agent.process_message(context_message, phone_number, 'hybrid')
            if ai_result and ai_result.get("status") == "success":
                return ai_result.get("reply_sent", "Maaf, ada kesalahan dalam pemrosesan pesan.")

        # DB-backed fallback handlers per command
        if handler == "schedule":
            return self._handle_schedule_request()
        if handler == "location":
            return self._handle_location_request()
        if handler == "statistics":
            return self._handle_statistics_request(user_role)
        if handler == "points":
            return self._handle_points_request(phone_number)

        # Ultimate fallback: role-based help
        return self._get_help_message(phone_number)

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

        # Fallback response → role-based help
        return self._get_help_message(phone_number or "")

    def _handle_schedule_request(self) -> str:
        """Handle schedule request using database data"""
        try:
            rows = self.db_manager.execute_query(
                "SELECT point_id, day_of_week, start_time, end_time FROM collection_schedules WHERE is_active = 1 ORDER BY day_of_week LIMIT 10"
            )
            if not rows:
                return "Maaf, belum ada jadwal pengumpulan yang terdaftar."

            lines = ["Jadwal Pengumpulan Aktif:"]
            for r in rows:
                lines.append(
                    f"• {r.get('day_of_week')} {r.get('start_time')}-{r.get('end_time')} (Point: {r.get('point_id')})"
                )
            return "\n".join(lines)
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "fetching schedules")
            return self.message_service.format_error_response("general_error")

    def _handle_location_request(self) -> str:
        """Handle location request using database data"""
        try:
            rows = self.db_manager.execute_query(
                "SELECT name, type, latitude, longitude, description FROM collection_points WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 10"
            )
            if not rows:
                return "Maaf, belum ada titik pengumpulan yang terdaftar."

            lines = ["Titik Pengumpulan Aktif:"]
            for r in rows:
                lines.append(
                    f"• {r.get('name')} ({r.get('type')}) — {r.get('latitude')}, {r.get('longitude')}"
                )
            return "\n".join(lines)
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "fetching locations")
            return self.message_service.format_error_response("general_error")

    def _handle_points_request(self, phone_number: str) -> str:
        """Handle points request"""
        return self.message_service.format_error_response("coming_soon")

    def _handle_redeem_request(self) -> str:
        """Handle redeem request"""
        return self.message_service.format_error_response("coming_soon")

    def _handle_statistics_request(self, user_role: str) -> str:
        """Handle statistics request using database aggregates"""
        try:
            users = self.db_manager.execute_query(
                "SELECT COUNT(*) as total_users, SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active_users FROM users"
            )
            total_users = users[0]["total_users"] if users else 0
            active_users = users[0]["active_users"] if users else 0

            cls = self.db_manager.execute_query(
                "SELECT waste_type, COUNT(*) as count FROM waste_classifications GROUP BY waste_type"
            )
            counts = {row.get("waste_type", "unknown"): row.get("count", 0) for row in cls}

            stats = {
                "active_users": active_users,
                "total_users": total_users,
                "organic_count": counts.get("ORGANIK", 0),
                "inorganic_count": counts.get("ANORGANIK", 0),
                "b3_count": counts.get("B3", 0),
            }
            return self.message_service.format_statistics_response(stats, user_role)
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "fetching statistics")
            return self.message_service.format_error_response("general_error")

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
        """Generate comprehensive, role-based help message using constants"""
        from core.constants import COMMAND_MAPPING, FEATURE_STATUS, USER_ROLES

        role = self.role_manager.get_user_role(phone_number) or "warga"

        # Determine enabled features for the role
        enabled_map = FEATURE_STATUS.get(role, {})

        # Resolve which commands are visible for this role
        def command_visible(cmd_key: str) -> bool:
            feature = COMMAND_MAPPING[cmd_key]["feature"]
            if role == "admin":
                return True
            return enabled_map.get(feature, False)

        # Build command list text
        lines = ["🤖 EcoBot - Daftar Fitur"]
        lines.append(f"Peran kamu: {USER_ROLES.get(role, {}).get('name', role.title())}")
        lines.append("")

        # Show AI Agent modes so users know the three available services
        lines.append("Mode Layanan AI:")
        lines.append("• /layanan-ecobot — Mode EcoBot Service (database only)")
        lines.append("• /general-ecobot — Mode General Waste Management")
        lines.append("• /hybrid-ecobot — Mode Hybrid (default)")
        lines.append("")

        # Group commands by feature for readability
        for cmd_key, meta in COMMAND_MAPPING.items():
            if command_visible(cmd_key):
                feature = meta.get("feature", "")
                description = meta.get("description", "")
                lines.append(f"• {cmd_key} — {description}")

        # Add usage tips
        lines.append("")
        lines.append("Cara pakai:")
        lines.append("• Ketik nama fitur langsung (tanpa /)")
        lines.append("• Kirim foto sampah untuk analisis AI")
        lines.append("• Tanya apa saja tentang pengelolaan sampah")

        # If admin, append concise Admin Panel commands
        if role == "admin":
            try:
                from core.admin_handler import AdminCommandHandler
                admin_handler = AdminCommandHandler(self.whatsapp_service, self.message_service)
                admin_help = admin_handler._admin_help()
                if admin_help.get("success") and admin_help.get("message"):
                    lines.append("")
                    lines.append("PANEL ADMIN:")
                    lines.append(admin_help["message"])
            except Exception:
                pass

        return "\n".join(lines)

    def _get_waste_education(self, waste_type: str) -> Dict[str, Any]:
        """Get education content for waste type"""
        education_data = self.message_service.get_education_messages()
        return education_data.get(waste_type.lower(), education_data.get("general", {}))
