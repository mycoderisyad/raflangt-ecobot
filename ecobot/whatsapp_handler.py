"""
WhatsApp Handler Module
Handles incoming and outgoing WhatsApp messages via Twilio with role-based access
"""

import os
import logging
from datetime import datetime
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import request

from .ai_classifier import AIClassifier
from .education_module import EducationModule
from .maps_integration import MapsIntegration
from .ai_conversation import AIConversation
from database.models import DatabaseManager, UserModel
from utils.helpers import is_image_message, download_image, validate_phone_number
from utils.message_loader import message_loader
from utils.role_manager import RoleManager, CommandParser
from utils.response_formatter import ResponseFormatter
from utils.admin_commands import AdminCommandHandler

logger = logging.getLogger(__name__)

class WhatsAppHandler:
    """Handle WhatsApp communication via Twilio with role-based access"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.whatsapp_number]):
            raise ValueError("Missing required Twilio credentials")
        
        self.client = Client(self.account_sid, self.auth_token)
        self.ai_classifier = AIClassifier()
        self.education_module = EducationModule()
        self.maps_integration = MapsIntegration()
        self.ai_conversation = AIConversation()
        self.messages = message_loader.get_whatsapp_messages()
        
        # Initialize role and response management
        self.db_manager = DatabaseManager()
        self.user_model = UserModel(self.db_manager)
        self.role_manager = RoleManager(self.user_model)
        self.command_parser = CommandParser(self.role_manager)
        self.response_formatter = ResponseFormatter()
        self.admin_handler = AdminCommandHandler()
        
        logger.info("WhatsApp Handler initialized with role management")
    
    def handle_incoming_message(self, request):
        """Process incoming WhatsApp message with role-based routing"""
        try:
            from_number = request.form.get('From')
            message_body = request.form.get('Body', '').strip()
            media_url = request.form.get('MediaUrl0')
            media_content_type = request.form.get('MediaContentType0')
            
            # Clean phone number format
            phone_number = from_number.replace('whatsapp:', '') if from_number else None
            
            # Create or update user in database
            user = self.user_model.create_or_update_user(phone_number)
            if not user:
                logger.error(f"Failed to create/update user: {phone_number}")
            
            response = MessagingResponse()
            
            # Handle image classification
            if media_url and self._is_image(media_content_type):
                reply = self._handle_image_classification(media_url, phone_number)
                self.user_model.increment_user_stats(phone_number, 'image')
            # Handle text commands
            elif message_body:
                reply = self._handle_text_command(message_body, phone_number)
                self.user_model.increment_user_stats(phone_number, 'message')
            # Default help message
            else:
                reply = self._get_help_message(phone_number)
            
            message = response.message()
            message.body(reply)
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            response = MessagingResponse()
            message = response.message()
            message.body(self.response_formatter.format_error_response('general_error'))
            return str(response)
    
    def _handle_image_classification(self, media_url, phone_number):
        """Handle waste classification from image using AI"""
        try:
            image_data = download_image(media_url)
            if not image_data:
                return self.response_formatter.format_error_response('general_error')
            
            # Use AI conversation for natural image analysis
            ai_analysis = self.ai_conversation.analyze_image(image_data)
            
            if ai_analysis:
                # Try to extract waste type for classification tracking
                waste_type = None
                try:
                    classification_result = self.ai_classifier.classify_waste_image(image_data)
                    if classification_result:
                        waste_type = classification_result['waste_type']
                        # Save classification to database
                        from database.models import WasteClassificationModel
                        waste_model = WasteClassificationModel(self.db_manager)
                        waste_model.save_classification(
                            phone_number, 
                            waste_type, 
                            classification_result['confidence'],
                            'ai'
                        )
                except Exception as e:
                    logger.warning(f"Classification tracking error: {str(e)}")
                
                return self.response_formatter.format_ai_response(ai_analysis, waste_type)
            else:
                # Fallback to traditional classification
                classification_result = self.ai_classifier.classify_waste_image(image_data)
                if not classification_result:
                    return self.response_formatter.format_error_response('general_error')
                
                # Save classification to database
                try:
                    from database.models import WasteClassificationModel
                    waste_model = WasteClassificationModel(self.db_manager)
                    waste_model.save_classification(
                        phone_number, 
                        classification_result['waste_type'], 
                        classification_result['confidence'],
                        'traditional'
                    )
                except Exception as e:
                    logger.warning(f"Classification save error: {str(e)}")
                
                education_content = self.education_module.get_waste_education(classification_result['waste_type'])
                return self.response_formatter.format_education_response(education_content)
                
        except Exception as e:
            logger.error(f"Image classification error: {str(e)}")
            return self.response_formatter.format_error_response('general_error')
    
    def _handle_text_command(self, message_body, phone_number):
        """Handle text-based commands with role-based routing"""
        try:
            # Check for admin commands first
            admin_command = self.admin_handler.parse_admin_command(message_body)
            if admin_command:
                return self.admin_handler.handle_admin_command(
                    admin_command['command'], 
                    admin_command['args'], 
                    phone_number
                )
            
            # Parse command with role checking
            command_info = self.command_parser.parse_command(message_body, phone_number)
            user_role = self.role_manager.get_user_role(phone_number)
            
            # Handle command based on status
            if command_info['status'] == 'no_permission':
                return self.response_formatter.format_error_response('no_permission', user_role)
            elif command_info['status'] == 'coming_soon':
                return self._handle_coming_soon_feature(command_info['command'])
            elif command_info['status'] == 'available':
                return self._route_available_command(command_info, phone_number, user_role)
            else:
                # General AI conversation
                return self._handle_general_conversation(message_body, phone_number)
                
        except Exception as e:
            logger.error(f"Text command error: {str(e)}")
            return self.response_formatter.format_error_response('general_error')
    
    def _route_available_command(self, command_info, phone_number, user_role):
        """Route command to appropriate handler"""
        command = command_info['command']
        
        if command == 'edukasi':
            return self._handle_education_request(command_info['message'])
        elif command == 'jadwal':
            return self._handle_schedule_request()
        elif command == 'lokasi':
            return self._handle_location_request()
        elif command == 'point':
            return self._handle_points_request(phone_number)
        elif command == 'redeem':
            return self._handle_redeem_request()
        elif command == 'statistik':
            return self._handle_statistics_request(user_role)
        elif command == 'laporan':
            return self._handle_report_request(phone_number, user_role)
        else:
            # General conversation or help
            if 'bantuan' in command_info['message'].lower() or 'help' in command_info['message'].lower():
                return self._get_help_message(phone_number)
            else:
                return self._handle_general_conversation(command_info['message'], phone_number)
    
    def _handle_education_request(self, message):
        """Handle education requests"""
        # Use AI conversation for natural education responses
        ai_response = self.ai_conversation.get_natural_response(message)
        if ai_response:
            return ai_response
        
        # Fallback to general education
        education_content = self.education_module.get_general_education()
        return self.response_formatter.format_education_response({'name': 'Tips Umum', 'description': education_content})
    
    def _handle_schedule_request(self):
        """Handle schedule requests"""
        # Get schedule data (mock for now)
        schedules = [
            {
                'location': 'Titik Pengumpulan Utama',
                'address': 'Jl. Raya Desa No. 123',
                'schedule': 'Senin, Rabu, Jumat - 08:00-10:00',
                'waste_types': 'Organik, Anorganik',
                'contact': '+62xxx'
            },
            {
                'location': 'Sekolah Dasar',
                'address': 'Jl. Pendidikan No. 45',
                'schedule': 'Selasa, Kamis - 14:00-16:00',
                'waste_types': 'Anorganik, Kertas',
                'contact': '+62xxx'
            }
        ]
        return self.response_formatter.format_schedule_response(schedules)
    
    def _handle_location_request(self):
        """Handle location requests"""
        try:
            locations = self.maps_integration.collection_points
            map_url = self.maps_integration.get_collection_points_map()
            return self.response_formatter.format_location_response(locations, map_url)
        except Exception as e:
            logger.error(f"Location request error: {str(e)}")
            return self.response_formatter.format_error_response('general_error')
    
    def _handle_points_request(self, phone_number):
        """Handle points requests (coming soon)"""
        user_data = self.user_model.get_user_stats(phone_number)
        return self.response_formatter.format_points_response(user_data or {})
    
    def _handle_redeem_request(self):
        """Handle redeem requests (coming soon)"""
        return self.response_formatter.format_redeem_response()
    
    def _handle_statistics_request(self, user_role):
        """Handle statistics requests"""
        # Mock statistics data
        stats = {
            'active_users': 45,
            'images_processed': 123,
            'successful_classifications': 118,
            'total_users': 67,
            'organic_count': 78,
            'inorganic_count': 45,
            'b3_count': 12,
            'system_status': 'Normal',
            'uptime': '99.8%'
        }
        return self.response_formatter.format_statistics_response(stats, user_role)
    
    def _handle_report_request(self, phone_number, user_role):
        """Handle report requests"""
        # Trigger email report generation
        try:
            from .email_notifications import EmailNotificationService
            email_service = EmailNotificationService()
            # This would trigger actual report generation
            # email_service.send_user_report(phone_number)
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
        
        return self.response_formatter.format_report_response(user_role)
    
    def _handle_coming_soon_feature(self, feature):
        """Handle coming soon features"""
        if feature == 'point':
            return self.response_formatter.format_points_response({})
        elif feature == 'redeem':
            return self.response_formatter.format_redeem_response()
        else:
            return self.response_formatter.format_error_response('coming_soon')
    
    def _handle_general_conversation(self, message, phone_number):
        """Handle general AI conversation"""
        try:
            ai_response = self.ai_conversation.get_natural_response(message)
            if ai_response:
                return ai_response
            else:
                return self.response_formatter.format_error_response('invalid_command')
        except Exception as e:
            logger.error(f"AI conversation error: {str(e)}")
            return self.response_formatter.format_error_response('general_error')
    
    def _get_help_message(self, phone_number):
        """Get help message based on user role"""
        help_message = self.command_parser.get_help_message(phone_number)
        
        # Add admin commands for admin users
        if self.user_model.is_admin(phone_number):
            help_message += "\n\n🔧 *Perintah Admin:*\n"
            help_message += "• `/admin help` - Bantuan perintah admin\n"
            help_message += "• `/admin user_list` - Daftar pengguna\n"
            help_message += "• `/admin stats` - Statistik sistem\n"
            help_message += "• `/admin point_list` - Daftar titik pengumpulan\n"
            help_message += "\nKetik `/admin help` untuk daftar lengkap perintah admin."
        
        return help_message
    
    def _is_image(self, content_type):
        """Check if content type is an image"""
        return content_type and content_type.startswith('image/')
    
    def send_message(self, to_number, message):
        """Send WhatsApp message"""
        try:
            message = self.client.messages.create(
                from_=self.whatsapp_number,
                body=message,
                to=f'whatsapp:{to_number}'
            )
            logger.info(f"Message sent to {to_number}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
        
        reply = f"{help_msg.get('title', '*EcoBot - Asisten Pengelolaan Sampah*')}\n\n"

