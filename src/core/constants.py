"""Application-wide constants."""

WASTE_TYPES = {
    "ORGANIK": {
        "description": "Sampah yang dapat terurai secara alami",
        "bin_color": "hijau/coklat",
    },
    "ANORGANIK": {
        "description": "Sampah yang tidak dapat terurai secara alami",
        "bin_color": "biru/kuning",
    },
    "B3": {
        "description": "Bahan Berbahaya dan Beracun",
        "bin_color": "merah/khusus",
    },
}

USER_ROLES = ("admin", "koordinator", "warga")

FEATURE_ACCESS = {
    "warga": {"education", "schedule", "location", "image_analysis", "chat"},
    "koordinator": {"education", "schedule", "location", "image_analysis", "chat", "statistics", "report"},
    "admin": {"education", "schedule", "location", "image_analysis", "chat", "statistics", "report", "broadcast", "admin"},
}

SUPPORTED_IMAGE_MIMES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}

MAX_MESSAGE_LENGTH = 4096
