"""
Constants for EcoBot application
"""

# Application constants
APP_NAME = "EcoBot"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-powered waste management assistant"

# Supported waste types
WASTE_TYPES = {
    'ORGANIK': {
        'color': 'GREEN',
        'description': 'Sampah yang dapat terurai secara alami',
        'bin_color': 'hijau/coklat'
    },
    'ANORGANIK': {
        'color': 'BLUE',
        'description': 'Sampah yang tidak dapat terurai secara alami',
        'bin_color': 'biru/kuning'
    },
    'B3': {
        'color': 'RED',
        'description': 'Bahan Berbahaya dan Beracun',
        'bin_color': 'merah/khusus'
    }
}

# Supported image formats
SUPPORTED_IMAGE_FORMATS = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp'
]

SUPPORTED_IMAGE_EXTENSIONS = [
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp'
]

# File size limits (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_MESSAGE_LENGTH = 1000

# API timeouts (in seconds)
API_TIMEOUT = 30
IMAGE_DOWNLOAD_TIMEOUT = 30

# Default coordinates (Jakarta)
DEFAULT_COORDINATES = {
    'lat': -6.2088,
    'lng': 106.8456
}

# WhatsApp message limits
WHATSAPP_MESSAGE_LIMIT = 1600  # Characters

# Database constants
DATABASE_TIMEOUT = 30
MAX_RETRY_ATTEMPTS = 3

# Email templates
EMAIL_SUBJECTS = {
    'daily_report': "Laporan Harian EcoBot",
    'weekly_summary': "Ringkasan Mingguan EcoBot",
    'alert': "Alert EcoBot",
    'maintenance': "Maintenance EcoBot"
}

# Log levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Cache durations (in seconds)
CACHE_DURATIONS = {
    'education_content': 3600,  # 1 hour
    'collection_points': 1800,  # 30 minutes
    'user_stats': 300,  # 5 minutes
    'api_responses': 600  # 10 minutes
}

# Rate limiting
RATE_LIMITS = {
    'messages_per_user_per_hour': 50,
    'images_per_user_per_hour': 20,
    'api_calls_per_minute': 100
}

# Command keywords
COMMAND_KEYWORDS = {
    'help': ['help', 'bantuan', 'info', 'panduan'],
    'location': ['lokasi', 'maps', 'peta', 'titik', 'tempat'],
    'education': ['edukasi', 'tips', 'belajar', 'info'],
    'organic': ['organik', 'kompos', 'sisa makanan'],
    'inorganic': ['anorganik', 'plastik', 'kaleng', 'kertas'],
    'b3': ['b3', 'berbahaya', 'beracun', 'baterai', 'obat']
}

# Response templates
RESPONSE_TEMPLATES = {
    'welcome': """*Selamat datang di EcoBot!*

Saya adalah asisten AI untuk membantu pengelolaan sampah di {village_name}.

*Cara menggunakan:*
• Kirim foto sampah untuk identifikasi otomatis
• Ketik 'lokasi' untuk melihat titik pengumpulan
• Ketik 'edukasi' untuk tips pengelolaan sampah

Mulai dengan mengirim foto sampah yang ingin Anda identifikasi.""",

    'error': "Maaf, terjadi kesalahan. Silakan coba lagi.",
    
    'unsupported_media': "Maaf, format file tidak didukung. Silakan kirim gambar dengan format JPG, PNG, atau GIF.",
    
    'image_too_large': "Maaf, ukuran gambar terlalu besar. Maksimal 5MB.",
    
    'processing': "⏳ Sedang memproses gambar Anda...",
    
    'classification_failed': "Maaf, tidak dapat mengidentifikasi jenis sampah. Coba kirim foto yang lebih jelas."
}

# Collection point types
COLLECTION_POINT_TYPES = {
    'main': 'Titik Utama',
    'school': 'Titik Sekolah',
    'mosque': 'Titik Ibadah',
    'health': 'Titik Kesehatan',
    'commercial': 'Titik Komersial'
}

# Operating schedules
OPERATING_SCHEDULES = {
    'daily': 'Setiap hari',
    'weekdays': 'Senin-Jumat',
    'weekends': 'Sabtu-Minggu',
    'specific': 'Jadwal khusus'
}

# Priority levels
PRIORITY_LEVELS = {
    'low': 'LOW',
    'normal': 'NORMAL',
    'medium': 'MEDIUM',
    'high': 'HIGH',
    'critical': 'CRITICAL'
}

# System status
SYSTEM_STATUS = {
    'healthy': 'OK',
    'warning': 'WARNING',
    'error': 'ERROR',
    'maintenance': 'MAINTENANCE'
}

# Default village settings
DEFAULT_VILLAGE_SETTINGS = {
    'name': 'Desa Cukangkawung',
    'coordinates': DEFAULT_COORDINATES,
    'timezone': 'Asia/Jakarta',
    'language': 'id',
    'currency': 'IDR'
}

# AI model settings
AI_MODEL_SETTINGS = {
    'confidence_threshold': 0.7,
    'max_retries': 3,
    'fallback_enabled': True,
    'mock_mode': False
}

# Security settings
SECURITY_SETTINGS = {
    'max_requests_per_minute': 60,
    'allowed_file_types': SUPPORTED_IMAGE_FORMATS,
    'max_file_size': MAX_IMAGE_SIZE,
    'sanitize_inputs': True
}

# Feature flags
FEATURE_FLAGS = {
    'points_system': False,  # Coming soon
    'user_profiles': False,  # Coming soon
    'analytics_dashboard': False,  # Coming soon
    'multi_language': False,  # Coming soon
    'voice_messages': False  # Future feature
}

# User roles and permissions
USER_ROLES = {
    'warga': {
        'name': 'Warga',
        'permissions': ['view_education', 'view_schedule', 'view_location', 'view_points'],
        'features': ['edukasi', 'jadwal', 'lokasi', 'point']
    },
    'koordinator': {
        'name': 'Koordinator',
        'permissions': ['view_education', 'view_schedule', 'view_location', 'view_points', 'view_statistics', 'generate_reports'],
        'features': ['edukasi', 'jadwal', 'lokasi', 'point', 'statistik', 'laporan']
    },
    'admin': {
        'name': 'Admin',
        'permissions': ['all'],
        'features': ['all']
    }
}

# Feature status
FEATURE_STATUS = {
    'edukasi': 'active',
    'jadwal': 'active', 
    'lokasi': 'active',
    'point': 'coming_soon',
    'redeem': 'coming_soon',
    'statistik': 'active',
    'laporan': 'active'
}

# Command mapping
COMMAND_MAPPING = {
    'edukasi': ['edukasi', 'tips', 'belajar', 'info', 'education'],
    'jadwal': ['jadwal', 'schedule', 'waktu', 'pengumpulan'],
    'lokasi': ['lokasi', 'maps', 'peta', 'titik', 'tempat', 'location'],
    'point': ['point', 'poin', 'skor', 'reward'],
    'redeem': ['redeem', 'tukar', 'hadiah', 'reward'],
    'statistik': ['statistik', 'stats', 'data'],
    'laporan': ['laporan', 'report', 'email', 'kirim']
}
