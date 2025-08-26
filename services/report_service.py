"""
Report Service
Handles report generation and email sending
"""

import threading
import logging
from datetime import datetime
from typing import Dict, Any
from services.email_service import EmailService
from core.utils import LoggerUtils


class ReportService:
    """Service for generating and sending reports"""

    def __init__(self, whatsapp_service=None):
        self.logger = LoggerUtils.get_logger(__name__)
        self.whatsapp_service = whatsapp_service
        self.email_service = EmailService()

    def generate_and_send_report_async(
        self, phone_number: str, user_role: str = "koordinator"
    ) -> Dict[str, Any]:
        """Generate and send PDF report via email asynchronously"""
        try:
            # Check if email service is properly configured
            if not self.email_service.mailry_api_key:
                return {
                    "success": False,
                    "message": "Error: Email service tidak dikonfigurasi dengan benar.\n\nPastikan MAILRY_API_KEY sudah diset di environment variables.",
                }

            # Start the report generation process
            initial_response = {
                "success": True,
                "message": f"""GENERATE LAPORAN EMAIL

Proses pembuatan laporan dimulai...

Laporan akan berisi:
• Statistik sistem dan kesehatan
• Data pengguna dan aktivitas
• Klasifikasi sampah hari ini
• Status titik pengumpulan
• Metrik performa sistem

Laporan PDF akan dikirim ke: {self.email_service.to_email}

Mohon tunggu 2-3 menit untuk proses pengiriman.

Status: Generating PDF...""",
            }

            # Generate and send report asynchronously (in background)
            def generate_report_async():
                try:
                    success = self.email_service.generate_and_send_report(phone_number)

                    if success:
                        # Send confirmation message
                        confirmation_msg = f"""LAPORAN BERHASIL DIKIRIM

Laporan PDF telah berhasil dikirim ke: {self.email_service.to_email}

Waktu pengiriman: {datetime.now().strftime('%d/%m/%Y %H:%M')} WIB

Silakan cek email Anda untuk melihat laporan lengkap.

Jika tidak menerima email dalam 10 menit, periksa folder spam atau hubungi support.

Status: Email Sent Successfully"""

                        # Send follow-up confirmation via WhatsApp
                        if self.whatsapp_service:
                            self.whatsapp_service.send_message(
                                phone_number, confirmation_msg
                            )
                    else:
                        # Send error message
                        error_msg = f"""GAGAL MENGIRIM LAPORAN

Terjadi kesalahan saat mengirim laporan email.

Waktu: {datetime.now().strftime('%d/%m/%Y %H:%M')} WIB

Silakan coba lagi atau hubungi support jika masalah berlanjut.

Status: Email Failed"""

                        if self.whatsapp_service:
                            self.whatsapp_service.send_message(phone_number, error_msg)

                except Exception as e:
                    error_msg = f"Error dalam background report generation: {str(e)}"
                    if self.whatsapp_service:
                        self.whatsapp_service.send_message(
                            phone_number, f"Laporan gagal dibuat: {error_msg}"
                        )

            # Start background thread
            report_thread = threading.Thread(target=generate_report_async)
            report_thread.daemon = True
            report_thread.start()

            return initial_response

        except Exception as e:
            return {"success": False, "message": f"Error generating report: {str(e)}"}

    def get_report_status(self, phone_number: str) -> Dict[str, Any]:
        """Get current report generation status"""
        try:
            # This could be enhanced to track actual report status
            return {
                "status": "processing",
                "message": "Report generation in progress",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "message": f"Error getting status: {str(e)}"}
