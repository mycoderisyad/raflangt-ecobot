"""
Response Formatter
Centralized response formatting utilities
"""

from typing import Dict, Any, List, Optional
from core.utils import MessageFormatter
from core.constants import ICONS


class ResponseFormatter:
    """Centralized response formatting utilities"""

    @staticmethod
    def format_success_response(message: str, data: Any = None) -> str:
        """Format success response"""
        response = MessageFormatter.format_success_header("Berhasil")
        response += f"{message}"

        if data:
            response += f"\n\nData: {data}"

        return response

    @staticmethod
    def format_error_response(
        error_type: str, user_role: str = "warga", details: str = None
    ) -> str:
        """Format error response"""
        error_messages = {
            "no_permission": {
                "title": "Akses Ditolak",
                "message": "Maaf, Anda tidak memiliki izin untuk mengakses fitur ini.\n\nSilakan hubungi admin untuk informasi lebih lanjut.",
            },
            "feature_disabled": {
                "title": "Fitur Dalam Maintenance",
                "message": "Fitur ini sedang dalam pemeliharaan.\n\nSilakan coba lagi nanti.",
            },
            "coming_soon": {
                "title": "Segera Hadir",
                "message": "Fitur ini akan segera tersedia.\n\nTerima kasih atas kesabaran Anda.",
            },
            "invalid_command": {
                "title": "Perintah Tidak Dikenali",
                "message": "Perintah tidak dikenali.\n\nSilakan ketik *help* untuk melihat daftar perintah yang tersedia.",
            },
            "general_error": {
                "title": "Terjadi Kesalahan",
                "message": "Terjadi kesalahan sistem.\n\nSilakan coba lagi atau hubungi admin jika masalah berlanjut.",
            },
            "registration_required": {
                "title": "Registrasi Diperlukan",
                "message": "Anda perlu mendaftar terlebih dahulu untuk menggunakan layanan ini.\n\nKetik *daftar* untuk memulai pendaftaran.",
            },
            "database_error": {
                "title": "Kesalahan Database",
                "message": "Terjadi kesalahan dalam sistem database.\n\nSilakan coba lagi atau hubungi admin.",
            },
            "api_error": {
                "title": "Kesalahan API",
                "message": "Terjadi kesalahan dalam layanan eksternal.\n\nSilakan coba lagi nanti.",
            },
            "validation_error": {
                "title": "Data Tidak Valid",
                "message": "Data yang Anda masukkan tidak valid.\n\nSilakan periksa dan coba lagi.",
            },
        }

        error_data = error_messages.get(error_type, error_messages["general_error"])
        response = (
            MessageFormatter.format_info_header(error_data["title"])
            + error_data["message"]
        )

        if details:
            response += f"\n\nDetail: {details}"

        return response

    @staticmethod
    def format_education_response(content: Dict[str, Any]) -> str:
        """Format education response"""
        if not content:
            return ResponseFormatter.format_error_response("general_error")

        response = MessageFormatter.format_info_header(
            "Tips Edukasi Pengelolaan Sampah"
        )

        if "tips" in content:
            response += "Tips Pengelolaan Sampah:\n\n"
            tips_formatted = []
            for i, tip in enumerate(content["tips"], 1):
                tips_formatted.append(f"{i}. {tip}")
            response += "\n".join(tips_formatted)
            response += "\n\n"

        if "additional_info" in content:
            response += "Informasi Tambahan:\n"
            response += content["additional_info"]

        return MessageFormatter.ensure_length_limit(response)

    @staticmethod
    def format_schedule_response(schedule_data: Dict[str, Any]) -> str:
        """Format schedule response"""
        response = MessageFormatter.format_info_header("Jadwal Pengumpulan Sampah")

        if not schedule_data:
            response += "Jadwal pengumpulan sampah akan diumumkan segera.\n\n"
            response += "Hubungi koordinator desa untuk informasi terbaru."
        else:
            response += "Jadwal pengumpulan sampah:\n\n"
            for day, info in schedule_data.items():
                response += f"• {day}: {info}\n"

        return MessageFormatter.ensure_length_limit(response)

    @staticmethod
    def format_location_response(location_data: Dict[str, Any]) -> str:
        """Format location response"""
        response = MessageFormatter.format_info_header("Lokasi Pengumpulan")

        if not location_data:
            response += "Data lokasi pengumpulan tidak tersedia."
        else:
            response += "Titik pengumpulan sampah terdekat:\n\n"
            for location in location_data.get("locations", []):
                response += f"• {location.get('name', 'Unknown')}\n"
                response += f"  Alamat: {location.get('address', 'N/A')}\n"
                response += f"  Jenis: {location.get('type', 'N/A')}\n\n"

        return MessageFormatter.ensure_length_limit(response)

    @staticmethod
    def format_statistics_response(stats: Dict[str, Any], user_role: str) -> str:
        """Format statistics response"""
        response = MessageFormatter.format_info_header("Statistik EcoBot")

        if user_role == "warga":
            return (
                response
                + "Fitur statistik hanya tersedia untuk Koordinator dan Admin.\n\nSilakan hubungi koordinator desa untuk informasi lebih lanjut."
            )

        response += "Data Hari Ini:\n"
        response += f"• Pengguna Aktif: {stats.get('active_users', 0)}\n"
        response += f"• Foto Dianalisis: {stats.get('images_processed', 0)}\n"
        response += (
            f"• Klasifikasi Berhasil: {stats.get('successful_classifications', 0)}\n\n"
        )

        response += "Data Minggu Ini:\n"
        response += f"• Total Pengguna: {stats.get('total_users', 0)}\n"
        response += f"• Sampah Organik: {stats.get('organic_count', 0)}\n"
        response += f"• Sampah Anorganik: {stats.get('inorganic_count', 0)}\n"
        response += f"• Sampah B3: {stats.get('b3_count', 0)}\n\n"

        if user_role == "admin":
            response += "Sistem:\n"
            response += f"• Status: {stats.get('system_status', 'Normal')}\n"
            response += f"• Uptime: {stats.get('uptime', '99.9%')}\n"

        return MessageFormatter.ensure_length_limit(response)

    @staticmethod
    def format_report_response(user_role: str) -> str:
        """Format report response"""
        response = MessageFormatter.format_info_header("Laporan EcoBot")

        if user_role == "warga":
            return (
                response
                + "Fitur laporan hanya tersedia untuk Koordinator dan Admin.\n\nSilakan hubungi koordinator desa untuk informasi lebih lanjut."
            )

        response += "Laporan PDF akan dikirim via email...\n\n"
        response += "Proses pembuatan laporan dimulai:\n"
        response += "• Mengumpulkan data sistem\n"
        response += "• Generating PDF report\n"
        response += "• Mengirim ke email admin\n\n"
        response += "Laporan berisi:\n"
        response += "• Statistik penggunaan harian\n"
        response += "• Data klasifikasi sampah\n"
        response += "• Analisis pengguna aktif\n"
        response += "• Status sistem kesehatan\n"
        response += "• Metrik performa\n\n"
        response += "Email akan diterima dalam 2-3 menit.\n"
        response += "Periksa inbox dan folder spam."

        return response

    @staticmethod
    def format_list_response(
        title: str, items: List[str], item_type: str = "item"
    ) -> str:
        """Format list response"""
        response = MessageFormatter.format_info_header(title)

        if not items:
            response += f"Tidak ada {item_type} yang tersedia."
        else:
            response += f"Daftar {item_type}:\n\n"
            for i, item in enumerate(items, 1):
                response += f"{i}. {item}\n"

        return MessageFormatter.ensure_length_limit(response)

    @staticmethod
    def format_table_response(
        title: str, headers: List[str], rows: List[List[str]]
    ) -> str:
        """Format table response"""
        response = MessageFormatter.format_info_header(title)

        if not rows:
            response += "Tidak ada data yang tersedia."
            return response

        # Add headers
        header_line = " | ".join(headers)
        response += f"{header_line}\n"
        response += "-" * len(header_line) + "\n"

        # Add rows
        for row in rows:
            row_line = " | ".join(str(cell) for cell in row)
            response += f"{row_line}\n"

        return MessageFormatter.ensure_length_limit(response)
