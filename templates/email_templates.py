"""
Email Templates Module
Template email yang terpisah untuk kemudahan maintenance
"""

from datetime import datetime, timedelta

class EmailTemplates:
    """Email templates untuk berbagai jenis notifikasi"""
    
    def __init__(self, village_name="Desa Cukangkawung"):
        self.village_name = village_name
    
    def daily_report_template(self, stats):
        """Template untuk laporan harian"""
        today = datetime.now().strftime('%d %B %Y')
        
        template = f"""
LAPORAN HARIAN ECOBOT
{self.village_name}
Tanggal: {today}

===============================

STATISTIK HARI INI:
• Total Pesan WhatsApp: {stats.get('total_messages', 0)}
• Foto Sampah Dianalisis: {stats.get('images_processed', 0)}
• Klasifikasi Organik: {stats.get('organic_count', 0)}
• Klasifikasi Anorganik: {stats.get('inorganic_count', 0)}
• Klasifikasi B3: {stats.get('b3_count', 0)}
• Permintaan Lokasi: {stats.get('location_requests', 0)}
• Permintaan Edukasi: {stats.get('education_requests', 0)}

👥 PENGGUNA AKTIF:
• Pengguna Baru: {stats.get('new_users', 0)}
• Pengguna Aktif: {stats.get('active_users', 0)}
• Total Pengguna: {stats.get('total_users', 0)}

🎯 TINGKAT AKURASI:
• Akurasi Klasifikasi: {stats.get('accuracy_rate', 95.0):.1f}%
• Tingkat Respons: {stats.get('response_rate', 98.0):.1f}%

⚠ MASALAH YANG TERDETEKSI:
{self._format_issues(stats.get('issues', []))}

📈 TREN:
• Perubahan dari kemarin: {stats.get('daily_change', '+5')}%
• Jenis sampah terpopuler: {stats.get('popular_waste_type', 'Anorganik')}

===============================

Laporan ini dibuat otomatis oleh sistem EcoBot.
Untuk informasi lebih lanjut, silakan hubungi tim teknis.

EcoBot - Membangun lingkungan yang lebih bersih 🌱
        """.strip()
        
        return template
    
    def weekly_summary_template(self, stats):
        """Template untuk ringkasan mingguan"""
        week_start = (datetime.now() - timedelta(days=7)).strftime('%d %B %Y')
        week_end = datetime.now().strftime('%d %B %Y')
        
        template = f"""
RINGKASAN MINGGUAN ECOBOT
{self.village_name}
Periode: {week_start} - {week_end}

===============================

STATISTIK MINGGU INI:
• Total Pesan: {stats.get('weekly_messages', 0)}
• Total Gambar Diproses: {stats.get('weekly_images', 0)}
• Total Pengguna Aktif: {stats.get('weekly_active_users', 0)}

📈 DISTRIBUSI JENIS SAMPAH:
• Organik: {stats.get('weekly_organic', 0)} ({stats.get('organic_percentage', 0):.1f}%)
• Anorganik: {stats.get('weekly_inorganic', 0)} ({stats.get('inorganic_percentage', 0):.1f}%)
• B3: {stats.get('weekly_b3', 0)} ({stats.get('b3_percentage', 0):.1f}%)

🎯 METRIK KINERJA:
• Waktu Respons Rata-rata: {stats.get('avg_response_time', 2.5):.1f} detik
• Tingkat Kepuasan: {stats.get('satisfaction_rate', 92.0):.1f}%
• Uptime Sistem: {stats.get('system_uptime', 99.5):.1f}%

🏆 PENCAPAIAN:
• Sampah Terklasifikasi: {stats.get('total_classified', 0)} item
• Edukasi Diberikan: {stats.get('education_provided', 0)} sesi
• Lokasi Ditampilkan: {stats.get('locations_shown', 0)} kali

TITIK PENGUMPULAN POPULER:
{self._format_popular_locations(stats.get('popular_locations', []))}

MAINTENANCE & UPDATES:
{self._format_maintenance_notes(stats.get('maintenance_notes', []))}

===============================

Terima kasih atas dukungan Anda dalam program digitalisasi
pengelolaan sampah {self.village_name}.

EcoBot - Teknologi untuk Lingkungan Berkelanjutan
        """.strip()
        
        return template
    
    def alert_notification_template(self, alert_type, message, priority):
        """Template untuk notifikasi alert"""
        timestamp = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        priority_icon = "HIGH" if priority == "high" else "MEDIUM" if priority == "medium" else "LOW"
        
        template = f"""
ALERT ECOBOT SYSTEM
{self.village_name}

{priority_icon} TINGKAT PRIORITAS: {priority.upper()}
WAKTU: {timestamp}
JENIS: {alert_type}

===============================

DETAIL ALERT:
{message}

===============================

TINDAKAN YANG DIPERLUKAN:
{self._get_alert_actions(alert_type)}

⚠ ALERT ini memerlukan perhatian segera.
Silakan periksa sistem EcoBot dan ambil tindakan yang diperlukan.

Tim Teknis EcoBot
        """.strip()
        
        return template
    
    def user_report_template(self, user_phone, user_stats):
        """Template untuk laporan pengguna individu"""
        today = datetime.now().strftime('%d %B %Y')
        
        template = f"""
LAPORAN AKTIVITAS ECOBOT
Pengguna: {user_phone}
Tanggal: {today}

===============================

AKTIVITAS ANDA:
• Total Pesan Dikirim: {user_stats.get('total_messages', 0)}
• Foto Sampah Dianalisis: {user_stats.get('images_sent', 0)}
• Akurasi Klasifikasi: {user_stats.get('accuracy_rate', 95.0):.1f}%

♻️ KONTRIBUSI LINGKUNGAN:
• Sampah Organik Teridentifikasi: {user_stats.get('organic_identified', 0)}
• Sampah Anorganik Teridentifikasi: {user_stats.get('inorganic_identified', 0)}
• Sampah B3 Teridentifikasi: {user_stats.get('b3_identified', 0)}

🎯 PENCAPAIAN:
• Hari Aktif: {user_stats.get('active_days', 0)}
• Tips Edukasi Diterima: {user_stats.get('education_received', 0)}
• Lokasi Dicari: {user_stats.get('location_searches', 0)}

===============================

Terima kasih telah menggunakan EcoBot untuk pengelolaan sampah!
Kontribusi Anda membantu menjaga kebersihan {self.village_name}.

EcoBot - Bersama Membangun Lingkungan Bersih 🌱
        """.strip()
        
        return template
    
    def system_maintenance_template(self, maintenance_info):
        """Template untuk notifikasi maintenance"""
        scheduled_time = maintenance_info.get('scheduled_time', 'TBD')
        duration = maintenance_info.get('duration', '2 jam')
        
        template = f"""
PEMBERITAHUAN MAINTENANCE SISTEM
ECOBOT {self.village_name}

===============================

JADWAL MAINTENANCE:
• Waktu: {scheduled_time}
• Durasi Estimasi: {duration}
• Jenis: {maintenance_info.get('type', 'Maintenance Rutin')}

PEKERJAAN YANG DILAKUKAN:
{self._format_maintenance_tasks(maintenance_info.get('tasks', []))}

⚠ DAMPAK LAYANAN:
• EcoBot WhatsApp: {maintenance_info.get('whatsapp_impact', 'Tidak tersedia sementara')}
• AI Classification: {maintenance_info.get('ai_impact', 'Menggunakan mode fallback')}
• Database: {maintenance_info.get('db_impact', 'Read-only mode')}

KONTAK DARURAT:
• Email: {maintenance_info.get('emergency_email', 'admin@ecobot.local')}
• WhatsApp Admin: {maintenance_info.get('emergency_phone', '+62xxx')}

===============================

Mohon maaf atas ketidaknyamanan yang mungkin terjadi.
Kami berkomitmen untuk meningkatkan kualitas layanan EcoBot.

Tim Teknis EcoBot
        """.strip()
        
        return template
    
    def monthly_analytics_template(self, stats):
        """Template untuk laporan analitik bulanan"""
        month_year = datetime.now().strftime('%B %Y')
        
        template = f"""
LAPORAN ANALITIK BULANAN
ECOBOT {self.village_name}
Periode: {month_year}

===============================

RINGKASAN BULANAN:
• Total Interaksi: {stats.get('monthly_interactions', 0):,}
• Foto Diproses: {stats.get('monthly_images', 0):,}
• Pengguna Aktif: {stats.get('monthly_active_users', 0):,}
• Tingkat Retensi: {stats.get('retention_rate', 75.0):.1f}%

📈 TREN PENGGUNAAN:
• Pertumbuhan Pengguna: {stats.get('user_growth', 15.5):.1f}%
• Peningkatan Akurasi: {stats.get('accuracy_improvement', 2.3):.1f}%
• Waktu Respons Rata-rata: {stats.get('avg_response_time', 1.8):.1f} detik

♻️ DAMPAK LINGKUNGAN:
• Total Sampah Terklasifikasi: {stats.get('total_classified', 0):,} item
• Estimasi CO2 Reduced: {stats.get('co2_saved', 245.7):.1f} kg
• Edukasi Lingkungan: {stats.get('education_sessions', 0):,} sesi

🏆 TOP PERFORMERS:
{self._format_top_performers(stats.get('top_users', []))}

🎯 REKOMENDASI:
{self._format_recommendations(stats.get('recommendations', []))}

===============================

Laporan analitik lengkap tersedia di dashboard admin.
Data diolah dengan memperhatikan privasi pengguna.

EcoBot Analytics Team
        """.strip()
        
        return template
    
    # Helper methods untuk formatting
    def _format_issues(self, issues):
        """Format daftar masalah"""
        if not issues:
            return '• Tidak ada masalah terdeteksi'
        
        formatted = []
        for issue in issues:
            formatted.append(f"• {issue}")
        
        return "\n".join(formatted)
    
    def _format_popular_locations(self, locations):
        """Format lokasi populer"""
        if not locations:
            return '• Data tidak tersedia'
        
        formatted = []
        for i, location in enumerate(locations[:5], 1):
            formatted.append(f"{i}. {location.get('name', 'Unknown')} - {location.get('visits', 0)} kunjungan")
        
        return "\n".join(formatted)
    
    def _format_maintenance_notes(self, notes):
        """Format catatan maintenance"""
        if not notes:
            return '• Tidak ada update maintenance'
        
        formatted = []
        for note in notes:
            formatted.append(f"• {note}")
        
        return "\n".join(formatted)
    
    def _format_maintenance_tasks(self, tasks):
        """Format tugas maintenance"""
        if not tasks:
            return '• Update sistem rutin'
        
        formatted = []
        for task in tasks:
            formatted.append(f"• {task}")
        
        return "\n".join(formatted)
    
    def _format_top_performers(self, users):
        """Format top performing users"""
        if not users:
            return '• Data tidak tersedia'
        
        formatted = []
        for i, user in enumerate(users[:5], 1):
            formatted.append(f"{i}. {user.get('phone', 'Anonymous')} - {user.get('interactions', 0)} interaksi")
        
        return "\n".join(formatted)
    
    def _format_recommendations(self, recommendations):
        """Format rekomendasi sistem"""
        if not recommendations:
            return '• Tidak ada rekomendasi khusus'
        
        formatted = []
        for rec in recommendations:
            formatted.append(f"• {rec}")
        
        return "\n".join(formatted)
    
    def _get_alert_actions(self, alert_type):
        """Dapatkan tindakan yang direkomendasikan untuk setiap jenis alert"""
        actions = {
            'system_error': '1. Periksa log sistem\n2. Restart service jika diperlukan\n3. Monitor kinerja',
            'high_load': '1. Monitor resource usage\n2. Scale up jika diperlukan\n3. Optimasi query',
            'api_failure': '1. Periksa koneksi API\n2. Validasi API keys\n3. Gunakan fallback jika tersedia',
            'database_error': '1. Periksa koneksi database\n2. Backup data\n3. Restore dari backup jika perlu',
            'user_spike': '1. Monitor kapasitas server\n2. Siapkan scaling\n3. Informasikan kepada tim',
            'security_breach': '1. Isolasi sistem yang terpengaruh\n2. Audit keamanan\n3. Reset kredensial',
            'storage_full': '1. Cleanup file temporary\n2. Archive data lama\n3. Upgrade storage',
            'network_issue': '1. Periksa koneksi internet\n2. Test endpoint API\n3. Gunakan backup connection',
            'default': '1. Investigasi masalah\n2. Ambil tindakan korektif\n3. Monitor situasi'
        }
        
        return actions.get(alert_type, actions['default'])
    
    def get_html_wrapper(self, content):
        """Wrapper HTML untuk email"""
        html_template = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoBot Notification</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
        .content {{
            white-space: pre-line;
            font-size: 14px;
            line-height: 1.6;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            font-size: 12px;
            color: #888;
        }}
        .highlight {{
            background-color: #f0f8ff;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🌱 EcoBot</div>
            <div>Sistem Pengelolaan Sampah Pintar</div>
        </div>
        <div class="content">
{content}
        </div>
        <div class="footer">
            <p>Email ini dikirim otomatis oleh sistem EcoBot.<br>
            Jangan membalas email ini. Untuk bantuan, hubungi tim support.</p>
            <p>&copy; 2025 EcoBot - {self.village_name}</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return html_template
