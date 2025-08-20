"""
Email Notifications Module
Menggunakan Mailry.co untuk mengirim notifikasi email otomatis
"""

import os
import logging
import requests
import sys
from datetime import datetime, timedelta
import json
from utils.message_loader import message_loader

# Import email templates
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from templates.email_templates import EmailTemplates

logger = logging.getLogger(__name__)

class EmailNotifications:
    """Handle email notifications using Mailry.co API"""
    
    def __init__(self):
        self.api_key = os.getenv('MAILRY_API_KEY')
        self.from_email = os.getenv('MAILRY_FROM_EMAIL')
        self.to_email = os.getenv('MAILRY_TO_EMAIL')
        self.base_url = os.getenv('MAILRY_BASE_URL', 'https://api.mailry.co/ext')
        
        if not self.api_key:
            logger.warning("Mailry API key not found. Using mock email service.")
            self.use_mock = True
        else:
            self.use_mock = False
            
        self.village_name = os.getenv('VILLAGE_NAME', 'Desa Cukangkawung')
        self.email_messages = message_loader.get_email_templates()
        
        # Initialize email templates
        self.templates = EmailTemplates(self.village_name)
        
        logger.info("Email Notifications initialized")
    
    def send_daily_report(self, stats):
        """Send daily waste management report"""
        try:
            subject = f"Laporan Harian EcoBot - {self.village_name}"
            
            # Generate report content using template
            content = self.templates.daily_report_template(stats)
            
            return self._send_email(
                to_email=self.to_email,
                subject=subject,
                content=content,
                email_type='daily_report'
            )
            
        except Exception as e:
            logger.error(f"Error sending daily report: {str(e)}")
            return False
    
    def send_weekly_summary(self, stats):
        """Send weekly waste management summary"""
        try:
            subject = f"Ringkasan Mingguan EcoBot - {self.village_name}"
            
            # Generate summary content using template
            content = self.templates.weekly_summary_template(stats)
            
            return self._send_email(
                to_email=self.to_email,
                subject=subject,
                content=content,
                email_type='weekly_summary'
            )
            
        except Exception as e:
            logger.error(f"Error sending weekly summary: {str(e)}")
            return False
    
    def send_alert_notification(self, alert_type, message, priority='normal'):
        """Send alert notification to administrators"""
        try:
            subject = f"Alert EcoBot - {alert_type}"
            
            # Generate alert content using template
            content = self.templates.alert_notification_template(alert_type, message, priority)
            
            return self._send_email(
                to_email=self.to_email,
                subject=subject,
                content=content,
                email_type='alert',
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
            return False
    
    def send_user_report(self, user_phone, user_stats, user_email=None):
        """Send personalized report to user"""
        try:
            if not user_email:
                # Log untuk future implementation ketika collect user email
                logger.info(f"User report generated for {user_phone}: {user_stats}")
                return True
            
            subject = f"Laporan Aktivitas EcoBot - {user_phone}"
            
            # Generate user report using template
            content = self.templates.user_report_template(user_phone, user_stats)
            
            return self._send_email(
                to_email=user_email,
                subject=subject,
                content=content,
                email_type='user_report'
            )
            
        except Exception as e:
            logger.error(f"Error sending user report: {str(e)}")
            return False
    
    def send_maintenance_notification(self, maintenance_info):
        """Send system maintenance notification"""
        try:
            subject = f"Maintenance EcoBot - {maintenance_info.get('type', 'Scheduled')}"
            
            # Generate maintenance notification using template
            content = self.templates.system_maintenance_template(maintenance_info)
            
            return self._send_email(
                to_email=self.to_email,
                subject=subject,
                content=content,
                email_type='maintenance'
            )
            
        except Exception as e:
            logger.error(f"Error sending maintenance notification: {str(e)}")
            return False
    
    def send_monthly_analytics(self, stats):
        """Send monthly analytics report"""
        try:
            month_year = datetime.now().strftime('%B %Y')
            subject = f"Analytics EcoBot {month_year} - {self.village_name}"
            
            # Generate analytics report using template
            content = self.templates.monthly_analytics_template(stats)
            
            return self._send_email(
                to_email=self.to_email,
                subject=subject,
                content=content,
                email_type='analytics'
            )
            
        except Exception as e:
            logger.error(f"Error sending monthly analytics: {str(e)}")
            return False
    
    def _send_email(self, to_email, subject, content, email_type='general', priority='normal'):
        """Send email using Mailry API"""
        try:
            if self.use_mock:
                return self._mock_send_email(to_email, subject, content, email_type)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'from': {
                    'email': self.from_email,
                    'name': 'EcoBot System'
                },
                'to': [
                    {
                        'email': to_email,
                        'name': 'Administrator'
                    }
                ],
                'subject': subject,
                'html': self.templates.get_html_wrapper(content),
                'text': content,
                'tags': [email_type, 'ecobot', 'waste-management'],
                'priority': priority
            }
            
            response = requests.post(
                f"{self.base_url}/send",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email sent successfully: {result.get('message_id', 'unknown')}")
                return True
            else:
                logger.error(f"Email sending failed: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Email API request error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return False
    
    def _mock_send_email(self, to_email, subject, content, email_type):
        """Mock email sending for development"""
        logger.info(f"MOCK EMAIL SENT:")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Type: {email_type}")
        logger.info(f"Content preview: {content[:100]}...")
        return True
    
    def schedule_report(self, report_type, schedule_time):
        """Schedule automated reports (placeholder for future implementation)"""
        logger.info(f"Report scheduled: {report_type} at {schedule_time}")
        # This would integrate with a task scheduler like Celery
        return True
    
    def get_email_statistics(self):
        """Get email sending statistics"""
        # Placeholder for email analytics
        return {
            'emails_sent_today': 5,
            'emails_sent_week': 35,
            'delivery_rate': 98.5,
            'open_rate': 85.2,
            'last_sent': datetime.now().isoformat()
        }
    
    def send_custom_notification(self, subject, content, email_type='custom', priority='normal'):
        """Send custom notification with provided content"""
        try:
            return self._send_email(
                to_email=self.to_email,
                subject=subject,
                content=content,
                email_type=email_type,
                priority=priority
            )
        except Exception as e:
            logger.error(f"Error sending custom notification: {str(e)}")
            return False
    
    def test_email_connection(self):
        """Test email service connection"""
        try:
            test_content = "Test email connection dari EcoBot system."
            return self.send_custom_notification(
                subject="🧪 Test Email EcoBot",
                content=test_content,
                email_type='test'
            )
        except Exception as e:
            logger.error(f"Email connection test failed: {str(e)}")
            return False
