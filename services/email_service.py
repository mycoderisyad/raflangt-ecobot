"""
Email Service
Handles email sending via Mailry.co service with PDF attachments
"""

import os
import json
import uuid
import random
import requests
import cloudscraper
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, List
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from core.utils import LoggerUtils
from database.models.system import SystemModel
from database.models.user import UserModel
from database.models.base import DatabaseManager


class EmailService:
    """Email service for sending reports via Mailry.co"""
    
    def __init__(self):
        self.logger = LoggerUtils.get_logger(__name__)
        self.mailry_api_key = os.getenv('MAILRY_API_KEY')
        self.mailry_base_url = os.getenv('MAILRY_BASE_URL', 'https://api.mailry.co/ext')
        self.from_email = os.getenv('MAILRY_FROM_EMAIL', 'noreply@mailsry.web.id')
        self.to_email = os.getenv('MAILRY_TO_EMAIL', 'supportecobot@mailsry.web.id')
        
        # Initialize models
        self.db_manager = DatabaseManager()
        self.system_model = SystemModel()
        self.user_model = UserModel(self.db_manager)
        
        # Create cloudscraper session for Cloudflare bypass
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        if not self.mailry_api_key:
            self.logger.error("MAILRY_API_KEY not found in environment variables")
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent to bypass Cloudflare"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        return random.choice(user_agents)
    
    def _get_request_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent"""
        return {
            'Authorization': f'Bearer {self.mailry_api_key}',
            'Content-Type': 'application/json',
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://mailry.co',
            'Referer': 'https://mailry.co/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def _make_request_with_retry(self, method: str, url: str, max_retries: int = 3, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and Cloudflare bypass using cloudscraper"""
        import time
        
        for attempt in range(max_retries):
            try:
                # Update headers for each attempt
                if 'headers' in kwargs:
                    kwargs['headers']['User-Agent'] = self._get_random_user_agent()
                
                # Add random delay to mimic human behavior
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(1.0, 3.0)
                    self.logger.info(f"Retrying request after {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                
                # Make request with cloudscraper session
                self.logger.info(f"Making {method} request to {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.request(method, url, timeout=45, **kwargs)
                
                # Log response details for debugging
                self.logger.info(f"Response status: {response.status_code}")
                
                # Check for success or expected error responses
                if response.status_code in [200, 201, 400, 401, 422]:  # Include 201 Created and expected error codes
                    return response
                
                # Check if we're still getting blocked
                if response.status_code == 403:
                    response_text_lower = response.text.lower()
                    if any(indicator in response_text_lower for indicator in ['cloudflare', 'just a moment', 'checking your browser', 'access denied']):
                        self.logger.warning(f"Still blocked by Cloudflare on attempt {attempt + 1}, response preview: {response.text[:200]}")
                        continue
                    else:
                        # 403 but not from Cloudflare (auth issue, etc.)
                        self.logger.warning(f"403 error but not Cloudflare (possibly auth issue): {response.text[:200]}")
                        return response
                
                # For other status codes, return the response
                return response
                
            except cloudscraper.exceptions.CloudflareChallengeError as e:
                self.logger.warning(f"CloudflareChallenge on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    self.logger.error("Failed to solve Cloudflare challenge after all attempts")
                    return None
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    self.logger.error(f"All {max_retries} attempts failed with request exception")
                    return None
            
            except Exception as e:
                self.logger.warning(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    self.logger.error(f"All {max_retries} attempts failed with unexpected error")
                    return None
        
        self.logger.error(f"All {max_retries} attempts failed")
        return None
    
    def generate_system_report_pdf(self) -> Optional[BytesIO]:
        """Generate PDF report with system statistics"""
        try:
            # Get report data
            report_data = self.system_model.get_daily_report()
            user_stats = report_data.get('user_stats', {})
            health = report_data.get('system_health', {})
            waste_stats = report_data.get('waste_classifications', {})
            collection_stats = report_data.get('collection_points', {})
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                alignment=TA_LEFT,
                textColor=colors.darkgreen
            )
            
            # Header
            story.append(Paragraph("EcoBot System Report", title_style))
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # System Health Section
            story.append(Paragraph("System Health Overview", subtitle_style))
            health_data = [
                ['Metric', 'Value', 'Status'],
                ['Overall Status', health.get('status', 'UNKNOWN'), '✓' if health.get('status') == 'EXCELLENT' else '⚠'],
                ['Health Score', f"{health.get('health_score', 0)}%", '✓' if health.get('health_score', 0) >= 90 else '⚠'],
                ['Interactions Today', str(health.get('activity', {}).get('interactions_today', 0)), '✓'],
                ['Classifications Today', str(health.get('activity', {}).get('classifications_today', 0)), '✓'],
                ['Errors Today', str(health.get('activity', {}).get('errors_today', 0)), '✓' if health.get('activity', {}).get('errors_today', 0) < 5 else '⚠']
            ]
            
            health_table = Table(health_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            health_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(health_table)
            story.append(Spacer(1, 0.3*inch))
            
            # User Statistics Section
            story.append(Paragraph("User Statistics", subtitle_style))
            user_data = [
                ['Metric', 'Count'],
                ['Total Users', str(user_stats.get('total_users', 0))],
                ['Admin Users', str(user_stats.get('admin_count', 0))],
                ['Coordinators', str(user_stats.get('koordinator_count', 0))],
                ['Citizens (Warga)', str(user_stats.get('warga_count', 0))],
                ['Registered Users', str(user_stats.get('registered_count', 0))],
                ['Pending Registration', str(user_stats.get('pending_count', 0))],
                ['Active Users', str(user_stats.get('active_count', 0))],
                ['Total Points Distributed', str(user_stats.get('total_points', 0) or 0)]
            ]
            
            user_table = Table(user_data, colWidths=[3*inch, 1.5*inch])
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(user_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Waste Classification Section
            if waste_stats:
                story.append(Paragraph("Waste Classification Today", subtitle_style))
                waste_data = [['Waste Type', 'Count', 'Avg Confidence']]
                
                for waste_type, stats in waste_stats.items():
                    waste_data.append([
                        waste_type.title(),
                        str(stats.get('count', 0)),
                        f"{stats.get('avg_confidence', 0):.1f}%"
                    ])
                
                waste_table = Table(waste_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                waste_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(waste_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Collection Points Section
            story.append(Paragraph("Collection Points", subtitle_style))
            collection_data = [
                ['Metric', 'Count'],
                ['Total Collection Points', str(collection_stats.get('total_points', 0))],
                ['Active Collection Points', str(collection_stats.get('active_points', 0))]
            ]
            
            collection_table = Table(collection_data, colWidths=[3*inch, 1.5*inch])
            collection_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(collection_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Footer
            footer_text = f"""
            <para align="center">
            <font size="10">
            This report was automatically generated by EcoBot System<br/>
            For more information, contact: {self.to_email}<br/>
            Report ID: {uuid.uuid4().hex[:8].upper()}
            </font>
            </para>
            """
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(footer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            self.logger.info("PDF report generated successfully")
            return buffer
            
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "generating PDF report")
            return None
    
    def upload_attachment_to_mailry(self, pdf_buffer: BytesIO) -> Optional[str]:
        """Upload PDF as attachment to Mailry and get attachment ID"""
        try:
            url = f"{self.mailry_base_url}/inbox/upload-attachment"
            
            # Prepare file upload
            files = {
                'file': ('ecobot_report.pdf', pdf_buffer.getvalue(), 'application/pdf')
            }
            
            headers = {
                'Authorization': f'Bearer {self.mailry_api_key}',
                'User-Agent': self._get_random_user_agent()
            }
            
            # Use retry mechanism
            response = self._make_request_with_retry('POST', url, files=files, headers=headers)
            
            if response and response.status_code in [200, 201]:  # 201 = Created
                result = response.json()
                # Handle both possible response formats
                attachment_id = result.get('id') or result.get('data', {}).get('id')
                self.logger.info(f"PDF uploaded successfully, attachment ID: {attachment_id}")
                return attachment_id
            elif response:
                self.logger.error(f"Failed to upload attachment: {response.status_code} - {response.text}")
                return None
            else:
                self.logger.error("Failed to upload attachment: No response received")
                return None
                
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "uploading attachment to Mailry")
            return None
    
    def send_report_email(self, attachment_id: str, user_phone: str = None) -> bool:
        """Send report email with PDF attachment"""
        try:
            # Generate unique email ID
            email_id = str(uuid.uuid4())
            
            # Prepare email content
            subject = f"EcoBot System Report - {datetime.now().strftime('%d %B %Y')}"
            
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #2c5530; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>EcoBot System Report</h1>
                    <p>Automated Daily Report - {datetime.now().strftime('%d %B %Y')}</p>
                </div>
                
                <div class="content">
                    <h2>Dear Administrator,</h2>
                    
                    <p>This is your automated daily system report for the EcoBot waste management system.</p>
                    
                    <h3>Report Contents:</h3>
                    <ul>
                        <li>System health overview and status</li>
                        <li>User statistics and engagement metrics</li>
                        <li>Waste classification data and accuracy</li>
                        <li>Collection point status and availability</li>
                        <li>Performance metrics and recommendations</li>
                    </ul>
                    
                    <p>The detailed report is attached as a PDF file. Please review the metrics and take any necessary actions based on the system status.</p>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Best regards,<br>
                    <strong>EcoBot System</strong></p>
                </div>
                
                <div class="footer">
                    <p>This email was automatically generated by EcoBot System on {datetime.now().strftime('%d %B %Y at %H:%M WIB')}</p>
                    <p>For support, contact: {self.to_email}</p>
                </div>
            </body>
            </html>
            """
            
            plain_body = f"""
            EcoBot System Report - {datetime.now().strftime('%d %B %Y')}
            
            Dear Administrator,
            
            This is your automated daily system report for the EcoBot waste management system.
            
            Report Contents:
            - System health overview and status
            - User statistics and engagement metrics  
            - Waste classification data and accuracy
            - Collection point status and availability
            - Performance metrics and recommendations
            
            The detailed report is attached as a PDF file. Please review the metrics and take any necessary actions based on the system status.
            
            If you have any questions or need assistance, please don't hesitate to contact our support team.
            
            Best regards,
            EcoBot System
            
            ---
            This email was automatically generated by EcoBot System on {datetime.now().strftime('%d %B %Y at %H:%M WIB')}
            For support, contact: {self.to_email}
            """
            
            # Prepare request payload according to Mailry API docs
            payload = {
                "to": self.to_email,
                "subject": subject,
                "htmlBody": html_body,
                "plainBody": plain_body,
                "attachments": [attachment_id]  # array of attachment IDs
            }
            
            # Send email
            url = f"{self.mailry_base_url}/inbox/send"
            headers = self._get_request_headers()
            
            # Use retry mechanism
            response = self._make_request_with_retry('POST', url, headers=headers, json=payload)
            
            if response and response.status_code in [200, 201]:  # 201 = Created (success)
                self.logger.info(f"Report email sent successfully to {self.to_email}")
                
                # Log the email sending event
                self.system_model.log_system_event(
                    'INFO',
                    f"Report email sent successfully to {self.to_email}",
                    'EmailService',
                    user_phone,
                    {'email_id': email_id, 'attachment_id': attachment_id}
                )
                
                return True
            elif response:
                self.logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
            else:
                self.logger.error("Failed to send email: No response received")
                return False
                
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "sending report email")
            return False
    
    def generate_and_send_report(self, user_phone: str = None) -> bool:
        """Generate PDF report and send via email"""
        try:
            self.logger.info("Starting report generation and email sending process")
            
            # Generate PDF
            pdf_buffer = self.generate_system_report_pdf()
            if not pdf_buffer:
                self.logger.error("Failed to generate PDF report")
                return False
            
            # Upload to Mailry
            attachment_id = self.upload_attachment_to_mailry(pdf_buffer)
            if not attachment_id:
                self.logger.error("Failed to upload PDF to Mailry")
                return False
            
            # Send email
            success = self.send_report_email(attachment_id, user_phone)
            
            # Clean up
            pdf_buffer.close()
            
            if success:
                self.logger.info("Report generation and email sending completed successfully")
            else:
                self.logger.error("Failed to send report email")
            
            return success
            
        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "generating and sending report")
            return False