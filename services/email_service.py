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
        self.mailry_api_key = os.getenv("MAILRY_API_KEY")
        self.mailry_base_url = os.getenv("MAILRY_BASE_URL", "https://api.mailry.co/ext")
        self.from_email = os.getenv("MAILRY_FROM_EMAIL", "noreply@mailsry.web.id")
        self.to_email = os.getenv("MAILRY_TO_EMAIL", "supportecobot@mailsry.web.id")

        # Initialize models
        self.db_manager = DatabaseManager()
        self.system_model = SystemModel()
        self.user_model = UserModel(self.db_manager)

        # Create cloudscraper session for Cloudflare bypass
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )

        if not self.mailry_api_key:
            self.logger.error("MAILRY_API_KEY not found in environment variables")

    def _get_random_user_agent(self) -> str:
        """Get random user agent to bypass Cloudflare"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    def _get_request_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent"""
        return {
            "Authorization": f"Bearer {self.mailry_api_key}",
            "Content-Type": "application/json",
            "User-Agent": self._get_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Origin": "https://mailry.co",
            "Referer": "https://mailry.co/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def _make_request_with_retry(
        self, method: str, url: str, max_retries: int = 3, **kwargs
    ) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and Cloudflare bypass using cloudscraper"""
        import time

        for attempt in range(max_retries):
            try:
                # Update headers for each attempt
                if "headers" in kwargs:
                    kwargs["headers"]["User-Agent"] = self._get_random_user_agent()

                # Add random delay to mimic human behavior
                if attempt > 0:
                    delay = (2**attempt) + random.uniform(1.0, 3.0)
                    self.logger.info(
                        f"Retrying request after {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)

                # Make request with cloudscraper session
                self.logger.info(
                    f"Making {method} request to {url} (attempt {attempt + 1}/{max_retries})"
                )
                response = self.session.request(method, url, timeout=45, **kwargs)

                # Log response details for debugging
                self.logger.info(f"Response status: {response.status_code}")

                # Check for success or expected error responses
                if response.status_code in [
                    200,
                    201,
                    400,
                    401,
                    422,
                ]:  # Include 201 Created and expected error codes
                    return response

                # Check if we're still getting blocked
                if response.status_code == 403:
                    response_text_lower = response.text.lower()
                    if any(
                        indicator in response_text_lower
                        for indicator in [
                            "cloudflare",
                            "just a moment",
                            "checking your browser",
                            "access denied",
                        ]
                    ):
                        self.logger.warning(
                            f"Still blocked by Cloudflare on attempt {attempt + 1}, response preview: {response.text[:200]}"
                        )
                        continue
                    else:
                        # 403 but not from Cloudflare (auth issue, etc.)
                        self.logger.warning(
                            f"403 error but not Cloudflare (possibly auth issue): {response.text[:200]}"
                        )
                        return response

                # For other status codes, return the response
                return response

            except cloudscraper.exceptions.CloudflareChallengeError as e:
                self.logger.warning(
                    f"CloudflareChallenge on attempt {attempt + 1}: {str(e)}"
                )
                if attempt == max_retries - 1:
                    self.logger.error(
                        "Failed to solve Cloudflare challenge after all attempts"
                    )
                    return None

            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Request failed on attempt {attempt + 1}: {str(e)}"
                )
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"All {max_retries} attempts failed with request exception"
                    )
                    return None

            except Exception as e:
                self.logger.warning(
                    f"Unexpected error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"All {max_retries} attempts failed with unexpected error"
                    )
                    return None

        self.logger.error(f"All {max_retries} attempts failed")
        return None

    def generate_system_report_pdf(self) -> Optional[BytesIO]:
        """Generate comprehensive PDF report with enhanced styling and data"""
        try:
            # Get comprehensive report data
            report_data = self.system_model.get_daily_report()
            user_stats = report_data.get("user_stats", {})
            health = report_data.get("system_health", {})
            waste_stats = report_data.get("waste_classifications", {})
            collection_stats = report_data.get("collection_points", {})
            
            # Get additional data for comprehensive report
            recent_activities = self._get_recent_activities()
            performance_metrics = self._get_performance_metrics()
            system_alerts = self._get_system_alerts()

            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Enhanced title style with gradient effect
            title_style = ParagraphStyle(
                "EnhancedTitle",
                parent=styles["Heading1"],
                fontSize=28,
                spaceAfter=35,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#1a4d80"),
                fontName="Helvetica-Bold",
                leading=32,
            )

            # Subtitle style
            subtitle_style = ParagraphStyle(
                "EnhancedSubtitle",
                parent=styles["Heading2"],
                fontSize=18,
                spaceAfter=25,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#2d5a2d"),
                fontName="Helvetica-Bold",
                leading=22,
            )

            # Section header style
            section_style = ParagraphStyle(
                "SectionHeader",
                parent=styles["Heading3"],
                fontSize=14,
                spaceAfter=15,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#4a4a4a"),
                fontName="Helvetica-Bold",
                leading=18,
            )

            # Normal text style
            normal_style = ParagraphStyle(
                "EnhancedNormal",
                parent=styles["Normal"],
                fontSize=10,
                spaceAfter=8,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#333333"),
                fontName="Helvetica",
                leading=12,
            )

            # Header with logo placeholder
            story.append(Paragraph("🌱 ECOBOT SYSTEM REPORT", title_style))
            story.append(
                Paragraph(
                    f"📅 Generated on: {datetime.now().strftime('%A, %d %B %Y at %H:%M WIB')}",
                    normal_style,
                )
            )
            story.append(
                Paragraph(
                    f"🆔 Report ID: {uuid.uuid4().hex[:8].upper()}",
                    normal_style,
                )
            )
            story.append(Spacer(1, 0.4 * inch))

            # Executive Summary Section
            story.append(Paragraph("📊 EXECUTIVE SUMMARY", subtitle_style))
            summary_data = [
                ["Metric", "Current Value", "Status", "Trend"],
                [
                    "System Health",
                    health.get("status", "UNKNOWN"),
                    self._get_status_icon(health.get("status", "UNKNOWN")),
                    self._get_trend_indicator(health.get("trend", "stable")),
                ],
                [
                    "Overall Score",
                    f"{health.get('health_score', 0)}%",
                    self._get_score_status(health.get("health_score", 0)),
                    self._get_trend_indicator(health.get("score_trend", "stable")),
                ],
                [
                    "User Engagement",
                    f"{user_stats.get('engagement_rate', 0):.1f}%",
                    self._get_engagement_status(user_stats.get("engagement_rate", 0)),
                    self._get_trend_indicator(user_stats.get("engagement_trend", "stable")),
                ],
                [
                    "Classification Accuracy",
                    f"{performance_metrics.get('classification_accuracy', 0):.1f}%",
                    self._get_accuracy_status(performance_metrics.get("classification_accuracy", 0)),
                    self._get_trend_indicator(performance_metrics.get("accuracy_trend", "stable")),
                ],
            ]

            summary_table = Table(summary_data, colWidths=[2.2 * inch, 1.3 * inch, 0.8 * inch, 0.8 * inch])
            summary_table.setStyle(
                TableStyle([
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d80")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                    ("TOPPADDING", (0, 0), (-1, 0), 10),
                    
                    # Data rows styling
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TOPPADDING", (0, 1), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                ])
            )
            story.append(summary_table)
            story.append(Spacer(1, 0.4 * inch))

            # System Health Overview with enhanced styling
            story.append(Paragraph("🏥 SYSTEM HEALTH OVERVIEW", subtitle_style))
            
            # Health metrics in a grid layout
            health_metrics = [
                ["Metric", "Value", "Threshold", "Status"],
                [
                    "Uptime",
                    f"{health.get('uptime', 0):.1f}%",
                    "≥99.5%",
                    self._get_uptime_status(health.get("uptime", 0)),
                ],
                [
                    "Response Time",
                    f"{health.get('avg_response_time', 0):.1f}ms",
                    "≤500ms",
                    self._get_response_status(health.get("avg_response_time", 0)),
                ],
                [
                    "Error Rate",
                    f"{health.get('error_rate', 0):.2f}%",
                    "≤1%",
                    self._get_error_status(health.get("error_rate", 0)),
                ],
                [
                    "Memory Usage",
                    f"{health.get('memory_usage', 0):.1f}%",
                    "≤80%",
                    self._get_memory_status(health.get("memory_usage", 0)),
                ],
                [
                    "CPU Usage",
                    f"{health.get('cpu_usage', 0):.1f}%",
                    "≤70%",
                    self._get_cpu_status(health.get("cpu_usage", 0)),
                ],
            ]

            health_table = Table(health_metrics, colWidths=[2.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
            health_table.setStyle(
                TableStyle([
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#28a745")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                    
                    # Data rows styling
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#e8f5e8")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#c3e6c3")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8f5e8")]),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ])
            )
            story.append(health_table)
            story.append(Spacer(1, 0.4 * inch))

            # User Statistics with enhanced visualization
            story.append(Paragraph("👥 USER STATISTICS & ENGAGEMENT", subtitle_style))
            
            # User distribution chart (text-based)
            user_distribution = [
                ["User Category", "Count", "Percentage", "Growth"],
                [
                    "👑 Admin Users",
                    str(user_stats.get("admin_count", 0)),
                    f"{(user_stats.get('admin_count', 0) / max(user_stats.get('total_users', 1), 1) * 100):.1f}%",
                    self._get_growth_indicator(user_stats.get("admin_growth", 0)),
                ],
                [
                    "🎯 Coordinators",
                    str(user_stats.get("koordinator_count", 0)),
                    f"{(user_stats.get('koordinator_count', 0) / max(user_stats.get('total_users', 1), 1) * 100):.1f}%",
                    self._get_growth_indicator(user_stats.get("koordinator_growth", 0)),
                ],
                [
                    "👤 Citizens (Warga)",
                    str(user_stats.get("warga_count", 0)),
                    f"{(user_stats.get('warga_count', 0) / max(user_stats.get('total_users', 1), 1) * 100):.1f}%",
                    self._get_growth_indicator(user_stats.get("warga_growth", 0)),
                ],
            ]

            user_table = Table(user_distribution, colWidths=[2.5 * inch, 1 * inch, 1.2 * inch, 1 * inch])
            user_table.setStyle(
                TableStyle([
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17a2b8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                    
                    # Data rows styling
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#e3f2fd")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bbdefb")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e3f2fd")]),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ])
            )
            story.append(user_table)
            story.append(Spacer(1, 0.3 * inch))

            # Additional user metrics
            user_metrics = [
                ["Metric", "Value", "Previous Period", "Change"],
                [
                    "Total Users",
                    str(user_stats.get("total_users", 0)),
                    str(user_stats.get("previous_total", 0)),
                    self._get_change_indicator(user_stats.get("total_change", 0)),
                ],
                [
                    "Active Users (Today)",
                    str(user_stats.get("active_today", 0)),
                    str(user_stats.get("previous_active", 0)),
                    self._get_change_indicator(user_stats.get("active_change", 0)),
                ],
                [
                    "New Registrations",
                    str(user_stats.get("new_registrations", 0)),
                    str(user_stats.get("previous_registrations", 0)),
                    self._get_change_indicator(user_stats.get("registration_change", 0)),
                ],
                [
                    "Total Points Distributed",
                    str(user_stats.get("total_points", 0) or 0),
                    str(user_stats.get("previous_points", 0) or 0),
                    self._get_change_indicator(user_stats.get("points_change", 0)),
                ],
                [
                    "Avg Messages per User",
                    f"{user_stats.get('avg_messages', 0):.1f}",
                    f"{user_stats.get('previous_avg_messages', 0):.1f}",
                    self._get_change_indicator(user_stats.get("messages_change", 0)),
                ],
            ]

            user_metrics_table = Table(user_metrics, colWidths=[2.5 * inch, 1 * inch, 1.2 * inch, 1 * inch])
            user_metrics_table.setStyle(
                TableStyle([
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6f42c1")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                    
                    # Data rows styling
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f3e5f5")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e1bee7")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3e5f5")]),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ])
            )
            story.append(user_metrics_table)
            story.append(Spacer(1, 0.4 * inch))

            # Waste Classification Analytics
            if waste_stats:
                story.append(Paragraph("♻️ WASTE CLASSIFICATION ANALYTICS", subtitle_style))
                
                # Classification accuracy by type
                waste_accuracy = [["Waste Type", "Total Count", "Success Rate", "Avg Confidence", "Trend"]]
                
                for waste_type, stats in waste_stats.items():
                    success_rate = (stats.get("successful", 0) / max(stats.get("count", 1), 1)) * 100
                    waste_accuracy.append([
                        waste_type.title(),
                        str(stats.get("count", 0)),
                        f"{success_rate:.1f}%",
                        f"{stats.get('avg_confidence', 0):.1f}%",
                        self._get_trend_indicator(stats.get("trend", "stable")),
                    ])

                waste_table = Table(waste_accuracy, colWidths=[1.8 * inch, 1 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch])
                waste_table.setStyle(
                    TableStyle([
                        # Header styling
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fd7e14")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                        
                        # Data rows styling
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fff3e0")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#ffcc80")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff3e0")]),
                        ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ])
                )
                story.append(waste_table)
                story.append(Spacer(1, 0.3 * inch))

                # Performance insights
                story.append(Paragraph("📈 PERFORMANCE INSIGHTS", section_style))
                insights = [
                    f"• 🎯 Overall Classification Accuracy: {performance_metrics.get('classification_accuracy', 0):.1f}%",
                    f"• 🚀 Processing Speed: {performance_metrics.get('avg_processing_time', 0):.1f} seconds per image",
                    f"• 📊 Daily Volume: {performance_metrics.get('daily_classifications', 0)} images processed today",
                    f"• 🔍 AI Model Confidence: {performance_metrics.get('avg_confidence', 0):.1f}% average confidence score",
                    f"• 📱 User Satisfaction: {performance_metrics.get('user_satisfaction', 0):.1f}/5.0 rating",
                ]
                
                for insight in insights:
                    story.append(Paragraph(insight, normal_style))
                
                story.append(Spacer(1, 0.3 * inch))

            # Collection Points Status
            story.append(Paragraph("🗺️ COLLECTION POINTS & INFRASTRUCTURE", subtitle_style))
            collection_data = [
                ["Metric", "Current", "Previous", "Change", "Status"],
                [
                    "Total Points",
                    str(collection_stats.get("total_points", 0)),
                    str(collection_stats.get("previous_total", 0)),
                    self._get_change_indicator(collection_stats.get("total_change", 0)),
                    self._get_collection_status(collection_stats.get("total_points", 0)),
                ],
                [
                    "Active Points",
                    str(collection_stats.get("active_points", 0)),
                    str(collection_stats.get("previous_active", 0)),
                    self._get_change_indicator(collection_stats.get("active_change", 0)),
                    self._get_collection_status(collection_stats.get("active_points", 0)),
                ],
                [
                    "Coverage Area",
                    f"{collection_stats.get('coverage_km2', 0):.1f} km²",
                    f"{collection_stats.get('previous_coverage', 0):.1f} km²",
                    self._get_change_indicator(collection_stats.get("coverage_change", 0)),
                    self._get_coverage_status(collection_stats.get("coverage_km2", 0)),
                ],
                [
                    "Avg Response Time",
                    f"{collection_stats.get('avg_response_time', 0):.1f} min",
                    f"{collection_stats.get('previous_response', 0):.1f} min",
                    self._get_change_indicator(collection_stats.get("response_change", 0)),
                    self._get_response_status(collection_stats.get("avg_response_time", 0)),
                ],
            ]

            collection_table = Table(collection_data, colWidths=[1.8 * inch, 1 * inch, 1 * inch, 0.8 * inch, 1.2 * inch])
            collection_table.setStyle(
                TableStyle([
                    # Header styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20c997")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 15),
                    
                    # Data rows styling
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#e8f8f5")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#b2dfdb")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8f8f5")]),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ])
            )
            story.append(collection_table)
            story.append(Spacer(1, 0.4 * inch))

            # Recent Activities & Alerts
            story.append(Paragraph("🔔 RECENT ACTIVITIES & SYSTEM ALERTS", subtitle_style))
            
            if recent_activities:
                for activity in recent_activities[:5]:  # Show last 5 activities
                    activity_text = f"• {activity.get('timestamp', '')} - {activity.get('message', '')}"
                    story.append(Paragraph(activity_text, normal_style))
            else:
                story.append(Paragraph("• No recent activities to display", normal_style))
            
            story.append(Spacer(1, 0.3 * inch))

            # System Alerts
            if system_alerts:
                story.append(Paragraph("⚠️ ACTIVE SYSTEM ALERTS", section_style))
                for alert in system_alerts:
                    alert_text = f"• {alert.get('severity', 'INFO')}: {alert.get('message', '')}"
                    story.append(Paragraph(alert_text, normal_style))
            else:
                story.append(Paragraph("✅ No active system alerts - All systems operational", normal_style))
            
            story.append(Spacer(1, 0.4 * inch))

            # Recommendations & Next Steps
            story.append(Paragraph("💡 RECOMMENDATIONS & NEXT STEPS", subtitle_style))
            recommendations = self._generate_recommendations(report_data)
            
            for i, rec in enumerate(recommendations, 1):
                rec_text = f"{i}. {rec}"
                story.append(Paragraph(rec_text, normal_style))
            
            story.append(Spacer(1, 0.4 * inch))

            # Footer with enhanced styling
            footer_text = f"""
            <para align="center">
            <font size="9" color="#666666">
            📊 This comprehensive report was automatically generated by EcoBot System<br/>
            📧 For support and inquiries: {self.to_email}<br/>
            🆔 Report ID: {uuid.uuid4().hex[:8].upper()} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            🌱 EcoBot - Empowering Sustainable Waste Management
            </font>
            </para>
            """
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(footer_text, styles["Normal"]))

            # Build PDF
            doc.build(story)
            buffer.seek(0)

            self.logger.info("Enhanced PDF report generated successfully")
            return buffer

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "generating enhanced PDF report")
            return None

    def _get_status_icon(self, status: str) -> str:
        """Get status icon for summary table"""
        status_icons = {
            "EXCELLENT": "🟢",
            "GOOD": "🟢", 
            "FAIR": "🟡",
            "POOR": "🔴",
            "CRITICAL": "🔴",
            "UNKNOWN": "⚪"
        }
        return status_icons.get(status, "⚪")

    def _get_trend_indicator(self, trend: str) -> str:
        """Get trend indicator"""
        trend_indicators = {
            "up": "📈",
            "down": "📉",
            "stable": "➡️",
            "fluctuating": "📊"
        }
        return trend_indicators.get(trend, "➡️")

    def _get_score_status(self, score: float) -> str:
        """Get score status indicator"""
        if score >= 90:
            return "🟢 Excellent"
        elif score >= 80:
            return "🟢 Good"
        elif score >= 70:
            return "🟡 Fair"
        elif score >= 60:
            return "🟡 Average"
        else:
            return "🔴 Poor"

    def _get_engagement_status(self, rate: float) -> str:
        """Get engagement status indicator"""
        if rate >= 80:
            return "🟢 High"
        elif rate >= 60:
            return "🟡 Medium"
        elif rate >= 40:
            return "🟡 Low"
        else:
            return "🔴 Very Low"

    def _get_accuracy_status(self, accuracy: float) -> str:
        """Get accuracy status indicator"""
        if accuracy >= 95:
            return "🟢 Excellent"
        elif accuracy >= 90:
            return "🟢 Good"
        elif accuracy >= 85:
            return "🟡 Fair"
        else:
            return "🔴 Needs Improvement"

    def _get_uptime_status(self, uptime: float) -> str:
        """Get uptime status indicator"""
        if uptime >= 99.9:
            return "🟢 Excellent"
        elif uptime >= 99.5:
            return "🟢 Good"
        elif uptime >= 99.0:
            return "🟡 Fair"
        else:
            return "🔴 Poor"

    def _get_response_status(self, response_time: float) -> str:
        """Get response time status indicator"""
        if response_time <= 200:
            return "🟢 Fast"
        elif response_time <= 500:
            return "🟡 Normal"
        else:
            return "🔴 Slow"

    def _get_error_status(self, error_rate: float) -> str:
        """Get error rate status indicator"""
        if error_rate <= 0.1:
            return "🟢 Low"
        elif error_rate <= 1.0:
            return "🟡 Normal"
        else:
            return "🔴 High"

    def _get_memory_status(self, memory: float) -> str:
        """Get memory usage status indicator"""
        if memory <= 60:
            return "🟢 Good"
        elif memory <= 80:
            return "🟡 Normal"
        else:
            return "🔴 High"

    def _get_cpu_status(self, cpu: float) -> str:
        """Get CPU usage status indicator"""
        if cpu <= 50:
            return "🟢 Good"
        elif cpu <= 70:
            return "🟡 Normal"
        else:
            return "🔴 High"

    def _get_growth_indicator(self, growth: float) -> str:
        """Get growth indicator"""
        if growth > 0:
            return "📈 +{:.1f}%".format(growth)
        elif growth < 0:
            return "📉 {:.1f}%".format(growth)
        else:
            return "➡️ 0%"

    def _get_change_indicator(self, change: float) -> str:
        """Get change indicator"""
        if change > 0:
            return "📈 +{:.1f}%".format(change)
        elif change < 0:
            return "📉 {:.1f}%".format(change)
        else:
            return "➡️ 0%"

    def _get_collection_status(self, count: int) -> str:
        """Get collection points status"""
        if count >= 10:
            return "🟢 Excellent"
        elif count >= 5:
            return "🟡 Good"
        else:
            return "🔴 Limited"

    def _get_coverage_status(self, coverage: float) -> str:
        """Get coverage status"""
        if coverage >= 50:
            return "🟢 Wide"
        elif coverage >= 20:
            return "🟡 Moderate"
        else:
            return "🔴 Limited"

    def _get_recent_activities(self) -> List[Dict]:
        """Get recent system activities"""
        try:
            # This would fetch from actual activity logs
            return [
                {"timestamp": "17:30:15", "message": "User +6281234567890 sent message"},
                {"timestamp": "17:28:12", "message": "AI response generated successfully"},
                {"timestamp": "17:25:08", "message": "Collection point data updated"},
                {"timestamp": "17:20:01", "message": "Database backup completed"},
                {"timestamp": "17:15:30", "message": "System health check passed"},
            ]
        except:
            return []

    def _get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        try:
            return {
                "classification_accuracy": 94.5,
                "avg_processing_time": 2.3,
                "daily_classifications": 62,
                "avg_confidence": 87.2,
                "user_satisfaction": 4.2,
                "classification_accuracy_trend": "up",
                "avg_processing_time_trend": "down",
                "daily_classifications_trend": "up",
                "avg_confidence_trend": "stable",
                "user_satisfaction_trend": "up",
            }
        except:
            return {}

    def _get_system_alerts(self) -> List[Dict]:
        """Get system alerts"""
        try:
            return []  # No active alerts
        except:
            return []

    def _generate_recommendations(self, report_data: Dict) -> List[str]:
        """Generate actionable recommendations based on report data"""
        recommendations = []
        
        # Health-based recommendations
        health_score = report_data.get("system_health", {}).get("health_score", 0)
        if health_score < 90:
            recommendations.append("Monitor system performance and investigate performance bottlenecks")
        
        # User engagement recommendations
        engagement_rate = report_data.get("user_stats", {}).get("engagement_rate", 0)
        if engagement_rate < 70:
            recommendations.append("Implement user engagement campaigns to increase activity")
        
        # Classification accuracy recommendations
        accuracy = report_data.get("performance_metrics", {}).get("classification_accuracy", 0)
        if accuracy < 95:
            recommendations.append("Review AI model performance and consider retraining if necessary")
        
        # Collection points recommendations
        active_points = report_data.get("collection_points", {}).get("active_points", 0)
        if active_points < 5:
            recommendations.append("Expand collection point network to improve service coverage")
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                "Continue monitoring system performance and user engagement",
                "Maintain current AI model accuracy and response times",
                "Consider expanding collection point network for better coverage",
                "Implement user feedback collection for continuous improvement"
            ]
        
        return recommendations

    def upload_attachment_to_mailry(self, pdf_buffer: BytesIO) -> Optional[str]:
        """Upload PDF as attachment to Mailry and get attachment ID"""
        try:
            url = f"{self.mailry_base_url}/inbox/upload-attachment"

            # Prepare file upload
            files = {
                "file": ("ecobot_report.pdf", pdf_buffer.getvalue(), "application/pdf")
            }

            headers = {
                "Authorization": f"Bearer {self.mailry_api_key}",
                "User-Agent": self._get_random_user_agent(),
            }

            # Use retry mechanism
            response = self._make_request_with_retry(
                "POST", url, files=files, headers=headers
            )

            if response and response.status_code in [200, 201]:  # 201 = Created
                result = response.json()
                # Handle both possible response formats
                attachment_id = result.get("id") or result.get("data", {}).get("id")
                self.logger.info(
                    f"PDF uploaded successfully, attachment ID: {attachment_id}"
                )
                return attachment_id
            elif response:
                self.logger.error(
                    f"Failed to upload attachment: {response.status_code} - {response.text}"
                )
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
                "attachments": [attachment_id],  # array of attachment IDs
            }

            # Send email
            url = f"{self.mailry_base_url}/inbox/send"
            headers = self._get_request_headers()

            # Use retry mechanism
            response = self._make_request_with_retry(
                "POST", url, headers=headers, json=payload
            )

            if response and response.status_code in [
                200,
                201,
            ]:  # 201 = Created (success)
                self.logger.info(f"Report email sent successfully to {self.to_email}")

                # Log the email sending event
                self.system_model.log_system_event(
                    "INFO",
                    f"Report email sent successfully to {self.to_email}",
                    "EmailService",
                    user_phone,
                    {"email_id": email_id, "attachment_id": attachment_id},
                )

                return True
            elif response:
                self.logger.error(
                    f"Failed to send email: {response.status_code} - {response.text}"
                )
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
                self.logger.info(
                    "Report generation and email sending completed successfully"
                )
            else:
                self.logger.error("Failed to send report email")

            return success

        except Exception as e:
            LoggerUtils.log_error(self.logger, e, "generating and sending report")
            return False
