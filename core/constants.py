"""
Application Constants
"""

# Waste Types
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

# User Roles and Permissions
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

# Feature Status
FEATURE_STATUS = {
    'warga': {
        'edukasi': True,
        'jadwal': True,
        'lokasi': True,
        'point': False,  # Coming soon
        'redeem': False,  # Coming soon
        'statistik': False,
        'laporan': False
    },
    'koordinator': {
        'edukasi': True,
        'jadwal': True,
        'lokasi': True,
        'point': False,  # Coming soon
        'redeem': False,  # Coming soon
        'statistik': True,
        'laporan': True
    },
    'admin': {
        'edukasi': True,
        'jadwal': True,
        'lokasi': True,
        'point': True,
        'redeem': True,
        'statistik': True,
        'laporan': True
    }
}

# Command Mapping
COMMAND_MAPPING = {
    'edukasi': {
        'aliases': ['edukasi', 'tips', 'belajar', 'info', 'education'],
        'handler': 'education',
        'feature': 'edukasi',
        'description': 'Tips dan edukasi pengelolaan sampah'
    },
    'jadwal': {
        'aliases': ['jadwal', 'schedule', 'waktu', 'pengumpulan'],
        'handler': 'schedule',
        'feature': 'jadwal',
        'description': 'Jadwal pengumpulan sampah'
    },
    'lokasi': {
        'aliases': ['lokasi', 'maps', 'peta', 'titik', 'tempat', 'location'],
        'handler': 'location',
        'feature': 'lokasi',
        'description': 'Lokasi titik pengumpulan sampah'
    },
    'point': {
        'aliases': ['point', 'poin', 'skor', 'cek'],
        'handler': 'points',
        'feature': 'point',
        'description': 'Cek poin dan sistem reward'
    },
    'daftar': {
        'aliases': ['daftar', 'register', 'signup'],
        'handler': 'register',
        'feature': 'point',
        'description': 'Daftar ke sistem poin'
    },
    'redeem': {
        'aliases': ['redeem', 'tukar', 'hadiah', 'reward'],
        'handler': 'redeem',
        'feature': 'redeem',
        'description': 'Tukar poin dengan hadiah'
    },
    'statistik': {
        'aliases': ['statistik', 'stats', 'data'],
        'handler': 'statistics',
        'feature': 'statistik',
        'description': 'Statistik sistem (koordinator)'
    },
    'laporan': {
        'aliases': ['laporan', 'report', 'email'],
        'handler': 'report',
        'feature': 'laporan',
        'description': 'Generate laporan (koordinator)'
    },
    'help': {
        'aliases': ['help', 'bantuan', 'menu', 'fitur'],
        'handler': 'help',
        'feature': 'edukasi',
        'description': 'Bantuan dan daftar fitur'
    }
}

# File Limits
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_MESSAGE_LENGTH = 1000
SUPPORTED_IMAGE_FORMATS = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# API Timeouts
DEFAULT_API_TIMEOUT = 30
IMAGE_PROCESSING_TIMEOUT = 60
EMAIL_SEND_TIMEOUT = 45

# Registration Status
REGISTRATION_STATUS = {
    'NEW': 'new',
    'PENDING': 'pending', 
    'REGISTERED': 'registered'
}

# Response Types
RESPONSE_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info'
}

# Icons (centralized for easy modification)
ICONS = {
    'SUCCESS': 'checkmark',
    'ERROR': 'cross',
    'WARNING': 'warning',
    'INFO': 'info',
    'ROBOT': 'robot',
    'EDUCATION': 'lightbulb',
    'SCHEDULE': 'calendar',
    'LOCATION': 'pin',
    'STATISTICS': 'chart',
    'REPORT': 'email',
    'POINTS': 'star'
}
