"""
Response Formatter
Membuat format balasan yang rapi dan terstruktur untuk WhatsApp
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Format responses untuk WhatsApp dengan struktur yang rapi"""
    
    def __init__(self):
        self.max_message_length = 1600  # WhatsApp limit
    
    def format_header(self, title: str, icon: str = "") -> str:
        """Format header dengan judul"""
        if icon:
            return f"{icon} *{title}*\n{'='*30}\n\n"
        return f"*{title}*\n{'='*20}\n\n"
    
    def format_section(self, title: str, content: str, icon: str = "") -> str:
        """Format section dengan judul dan konten"""
        section = ""
        if icon:
            section += f"{icon} *{title}*\n"
        else:
            section += f"*{title}*\n"
        section += f"{content}\n\n"
        return section
    
    def format_list(self, items: List[str], numbered: bool = False) -> str:
        """Format daftar item"""
        if not items:
            return ""
            
        formatted = ""
        for i, item in enumerate(items, 1):
            if numbered:
                formatted += f"{i}. {item}\n"
            else:
                formatted += f"• {item}\n"
        return formatted
    
    def format_table(self, data: Dict[str, str], separator: str = ":") -> str:
        """Format data dalam bentuk tabel sederhana"""
        formatted = ""
        for key, value in data.items():
            formatted += f"*{key}*{separator} {value}\n"
        return formatted
    
    def format_education_response(self, content: Dict[str, Any]) -> str:
        """Format respons edukasi"""
        response = self.format_header("Tips Pengelolaan Sampah", "💡")
        
        if 'name' in content:
            response += self.format_section("Jenis Sampah", content['name'])
        
        if 'description' in content:
            response += f"_{content['description']}_\n\n"
        
        if 'examples' in content:
            response += self.format_section("Contoh", self.format_list(content['examples']))
        
        if 'sorting_guide' in content:
            response += f"{content['sorting_guide']}\n\n"
        
        if 'recycling_tips' in content:
            response += f"{content['recycling_tips']}\n\n"
        
        response += "💬 *Ingin tahu lebih lanjut?* Tanya saja!"
        
        return self._ensure_length_limit(response)
    
    def format_schedule_response(self, schedules: List[Dict[str, Any]]) -> str:
        """Format respons jadwal pengumpulan"""
        response = self.format_header("Jadwal Pengumpulan Sampah", "📅")
        
        if not schedules:
            return response + "Maaf, belum ada jadwal yang tersedia."
        
        for i, schedule in enumerate(schedules, 1):
            response += f"*{i}. {schedule.get('location', 'Lokasi')}*\n"
            response += f"   📍 {schedule.get('address', 'Alamat tidak tersedia')}\n"
            response += f"   ⏰ {schedule.get('schedule', 'Jadwal belum ditentukan')}\n"
            response += f"   🗂️ {schedule.get('waste_types', 'Semua jenis sampah')}\n"
            
            if 'contact' in schedule:
                response += f"   📞 {schedule['contact']}\n"
            response += "\n"
        
        response += "📋 *Tips:* Siapkan sampah 30 menit sebelum jadwal pengumpulan"
        
        return self._ensure_length_limit(response)
    
    def format_location_response(self, locations: List[Dict[str, Any]], map_url: str = None) -> str:
        """Format respons lokasi"""
        response = self.format_header("Titik Pengumpulan Sampah", "📍")
        
        if not locations:
            return response + "Maaf, belum ada titik pengumpulan yang tersedia."
        
        for i, location in enumerate(locations, 1):
            response += f"*{i}. {location.get('name', 'Lokasi')}*\n"
            response += f"   📍 {location.get('type', 'Titik Pengumpulan')}\n"
            response += f"   🗂️ {', '.join(location.get('accepted_waste', []))}\n"
            response += f"   ⏰ {location.get('schedule', 'Setiap hari')}\n"
            
            if 'contact' in location:
                response += f"   📞 {location['contact']}\n"
            if 'description' in location:
                response += f"   ℹ️ {location['description']}\n"
            response += "\n"
        
        if map_url:
            response += f"🗺️ *Lihat di Peta:* {map_url}\n\n"
        
        response += "*Keterangan:*\n"
        response += "Organik | Anorganik | B3 (Berbahaya)\n\n"
        response += "📝 *Catatan:* Pastikan sampah bersih dan terpilah sebelum dibuang!"
        
        return self._ensure_length_limit(response)
    
    def format_points_response(self, user_data: Dict[str, Any]) -> str:
        """Format respons poin (coming soon)"""
        response = self.format_header("Sistem Poin EcoBot", "⭐")
        response += "🔜 *Fitur ini akan segera hadir!*\n\n"
        response += "Dengan sistem poin, Anda akan mendapatkan:\n"
        response += "• Poin setiap kali membuang sampah di titik pengumpulan\n"
        response += "• Reward menarik yang bisa ditukar\n"
        response += "• Leaderboard komunitas\n\n"
        response += "💡 *Mulai sekarang:*\n"
        response += "Kumpulkan sampah Anda dan buang di titik pengumpulan yang tersedia untuk bersiap mendapatkan poin!"
        
        return response
    
    def format_redeem_response(self) -> str:
        """Format respons redeem (coming soon)"""
        response = self.format_header("Tukar Hadiah", "🎁")
        response += "🔜 *Fitur ini akan segera hadir!*\n\n"
        response += "Hadiah yang akan tersedia:\n"
        response += "• Voucher belanja\n"
        response += "• Produk ramah lingkungan\n"
        response += "• Bibit tanaman\n"
        response += "• Merchandise EcoBot\n\n"
        response += "Tetap kumpulkan sampah untuk mendapatkan poin!"
        
        return response
    
    def format_statistics_response(self, stats: Dict[str, Any], user_role: str) -> str:
        """Format respons statistik"""
        response = self.format_header("Statistik EcoBot", "📊")
        
        if user_role == 'warga':
            return response + "⚠️ Fitur statistik hanya tersedia untuk Koordinator dan Admin.\n\nSilakan hubungi koordinator desa untuk informasi lebih lanjut."
        
        # For koordinator and admin
        response += "*Data Hari Ini:*\n"
        response += f"• Pengguna Aktif: {stats.get('active_users', 0)}\n"
        response += f"• Foto Dianalisis: {stats.get('images_processed', 0)}\n"
        response += f"• Klasifikasi Berhasil: {stats.get('successful_classifications', 0)}\n\n"
        
        response += "*Data Minggu Ini:*\n"
        response += f"• Total Pengguna: {stats.get('total_users', 0)}\n"
        response += f"• Sampah Organik: {stats.get('organic_count', 0)}\n"
        response += f"• Sampah Anorganik: {stats.get('inorganic_count', 0)}\n"
        response += f"• Sampah B3: {stats.get('b3_count', 0)}\n\n"
        
        if user_role == 'admin':
            response += "*Sistem:*\n"
            response += f"• Status: {stats.get('system_status', 'Normal')}\n"
            response += f"• Uptime: {stats.get('uptime', '99.9%')}\n"
        
        return self._ensure_length_limit(response)
    
    def format_report_response(self, user_role: str) -> str:
        """Format respons laporan"""
        response = self.format_header("Laporan EcoBot", "📧")
        
        if user_role == 'warga':
            return response + "⚠️ Fitur laporan hanya tersedia untuk Koordinator dan Admin.\n\nSilakan hubungi koordinator desa untuk informasi lebih lanjut."
        
        response += "✅ *Laporan sedang diproses...*\n\n"
        response += "Laporan akan dikirim ke email Anda dalam beberapa menit.\n\n"
        response += "*Isi Laporan:*\n"
        response += "• Statistik penggunaan\n"
        response += "• Data klasifikasi sampah\n"
        response += "• Analisis pengguna\n"
        response += "• Rekomendasi\n\n"
        response += "📧 Periksa email Anda dalam 5-10 menit."
        
        return response
    
    def format_error_response(self, error_type: str, user_role: str = 'warga') -> str:
        """Format respons error"""
        error_messages = {
            'no_permission': "⚠️ Maaf, Anda tidak memiliki izin untuk mengakses fitur ini.\n\nSilakan hubungi admin untuk informasi lebih lanjut.",
            'feature_disabled': "🔧 Fitur ini sedang dalam maintenance.\n\nSilakan coba lagi nanti.",
            'coming_soon': "🔜 Fitur ini akan segera hadir!\n\nTerima kasih atas kesabaran Anda.",
            'invalid_command': "❓ Perintah tidak dikenali.\n\nKetik 'bantuan' untuk melihat daftar perintah yang tersedia.",
            'general_error': "😔 Terjadi kesalahan. Silakan coba lagi atau hubungi admin jika masalah berlanjut."
        }
        
        return error_messages.get(error_type, error_messages['general_error'])
    
    def format_ai_response(self, ai_content: str, waste_type: str = None) -> str:
        """Format respons AI yang natural"""
        if waste_type:
            response = f"🤖 *Hasil Analisis: {waste_type.title()}*\n\n"
        else:
            response = "🤖 *EcoBot Assistant*\n\n"
        
        response += ai_content
        
        # Add helpful footer
        response += "\n\n💡 *Tips:* Tanya lebih lanjut atau kirim foto sampah lain untuk analisis!"
        
        return self._ensure_length_limit(response)
    
    def _ensure_length_limit(self, message: str) -> str:
        """Pastikan pesan tidak melebihi batas WhatsApp"""
        if len(message) <= self.max_message_length:
            return message
        
        # Truncate and add continuation message
        truncated = message[:self.max_message_length - 100]
        last_newline = truncated.rfind('\n')
        if last_newline > 0:
            truncated = truncated[:last_newline]
        
        truncated += "\n\n📱 *Pesan terpotong.* Tanya lebih spesifik untuk info lengkap."
        return truncated
    
    def format_welcome_message(self, user_name: str = None, role: str = 'warga') -> str:
        """Format pesan selamat datang"""
        greeting = "👋 *Selamat datang di EcoBot!*\n\n"
        
        if user_name:
            greeting += f"Halo {user_name}, "
        
        greeting += "Saya adalah asisten AI untuk membantu pengelolaan sampah.\n\n"
        
        greeting += "*🌟 Yang bisa saya bantu:*\n"
        greeting += "• 📸 Analisis jenis sampah dari foto\n"
        greeting += "• 💡 Tips pengelolaan sampah\n"
        greeting += "• 📍 Lokasi titik pengumpulan\n"
        greeting += "• 📅 Jadwal pengumpulan\n"
        
        if role in ['koordinator', 'admin']:
            greeting += "• 📊 Statistik dan laporan\n"
        
        greeting += "\n*🚀 Mulai dengan:*\n"
        greeting += "• Kirim foto sampah Anda\n"
        greeting += "• Ketik 'bantuan' untuk panduan lengkap\n"
        greeting += "• Tanya langsung tentang sampah\n\n"
        greeting += "Mari bersama-sama menjaga lingkungan! 🌱"
        
        return greeting
    
    def format_quick_help(self) -> str:
        """Format bantuan cepat dengan emoji minimal"""
        help_text = "*EcoBot - Bantuan Cepat*\n\n"
        help_text += "*Fitur Utama:*\n"
        help_text += "• Kirim *foto sampah* untuk analisis\n"
        help_text += "• Ketik *edukasi* untuk tips pengelolaan\n"
        help_text += "• Ketik *lokasi* untuk titik pengumpulan\n"
        help_text += "• Ketik *jadwal* untuk jadwal pengumpulan\n\n"
        help_text += "*Coming Soon:*\n"
        help_text += "• Sistem poin dan reward\n"
        help_text += "• Tukar hadiah\n\n"
        help_text += "Tanya apa saja tentang sampah!"
        
        return help_text
