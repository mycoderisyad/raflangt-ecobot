# EcoBot

Production-ready intelligent waste management system for community engagement through automated WhatsApp integration, AI-powered waste classification, and comprehensive administrative oversight.

## System Overview

EcoBot is a professional Flask-based backend platform engineered for scalable community waste management. The system integrates advanced AI classification, real-time collection coordination, and comprehensive administrative tools through a clean, minimal interface.

## Core Capabilities

- AI-powered waste classification and identification
- WhatsApp Business API integration for community access
- Role-based access control (Admin, Coordinator, Resident)
- Geographic collection point mapping and route optimization
- Real-time analytics and environmental impact assessment
- Administrative dashboard with clean, minimalist design
- Automated email reporting and notification system

## Technology Stack

| Component | Technology | Purpose | Status |
|-----------|------------|---------|--------|
| **Backend** | Flask + Python 3.10+ | REST API and core logic | Production-ready |
| **Database** | SQLite | Data persistence | Production-ready |
| **WhatsApp** | WAHA Integration | Message processing | Production-ready |
| **AI Services** | [Lunos.tech](https://lunos.tech/) & [Unli.dev](https://unli.dev/) | Waste classification | Production-ready |
| **Email** | [Mailry.co](https://mailry.co/) | Notifications and reports | Production-ready |
| **Web Server** | Gunicorn + Nginx | Production deployment | Production-ready |
| **Admin UI** | Flask + Jinja2 | Administrative interface | Production-ready |

## Getting Started

### Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)
- Valid API keys for WAHA, [Lunos.tech](https://lunos.tech/), and [Mailry.co](https://mailry.co/) services

### Installation

```bash
# Clone the repository
git clone https://github.com/mycoderisyad/raflangt-ecobot.git
cd raflangt-ecobot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment configuration
cp .env.example .env
# Edit .env file with your API keys and configuration
```

### Running the Application

```bash
# Development mode
python3 main.py

# Production mode
python3 main.py --production

# Production with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 'main:create_app("production")'
```

## System Components

### Main Application
- **Core Backend**: Flask-based REST API with health monitoring and webhook handling
- **Database**: SQLite database with user management, collection points, and schedules
- **Message Processing**: Automated WhatsApp message handling and AI-powered responses

### Admin Panel
- **Web Interface**: Clean, Notion-inspired administrative dashboard
- **User Management**: CRUD operations for user accounts and role assignment
- **Location Management**: Collection point mapping and waste type configuration
- **Schedule Management**: Collection schedule coordination and tracking
- **Analytics**: Real-time statistics and system monitoring

### API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|--------------|
| `/` | GET | Health check and service information |
| `/health` | GET | Detailed system health status |
| `/webhook` | POST | WhatsApp message webhook handler |

### Usage Workflow

1. **User Registration**: Community members register through WhatsApp
2. **Waste Classification**: Users send images for AI-powered waste identification
3. **Collection Coordination**: System provides collection schedules and locations
4. **Analytics**: Administrators monitor usage and environmental impact

## WhatsApp Bot Commands

## Warga (Citizen)

**Active Commands**
- daftar (register, signup) → Daftar ke sistem poin  
- edukasi (tips, belajar, info, education) → Tips dan edukasi pengelolaan sampah  
- jadwal (schedule, waktu, pengumpulan) → Jadwal pengumpulan sampah  
- lokasi (maps, peta, titik, tempat, location) → Lokasi titik pengumpulan sampah  
- help (bantuan, menu, fitur) → Bantuan dan daftar fitur  

**Coming Soon**
- point (poin, skor, cek) → Cek poin dan sistem reward  
- redeem (tukar, hadiah, reward) → Tukar poin dengan hadiah  

**Not Available**
- statistik  
- laporan  

---

## Koordinator (Coordinator)

Mendapat semua perintah Warga ditambah:

**Additional Commands**
- statistik (stats, data) → Statistik sistem  
- laporan (report, email) → Generate laporan  

**Coming Soon**
- point → Sistem poin  
- redeem → Sistem redeem  

---

## Admin (Administrator)

Mendapat semua perintah Warga dan Koordinator ditambah:

**Full Access**
- point → Akses penuh sistem poin  
- redeem → Akses penuh sistem redeem  
- /admin → Administrative command suite  

**Admin Special**
- /admin user_role → Kelola role pengguna  
- /admin report → Generate laporan sistem  

---

## Role Permission Summary

| Feature    | Warga       | Koordinator | Admin      |
|------------|-------------|-------------|------------|
| edukasi    | Active      | Active      | Active     |
| jadwal     | Active      | Active      | Active     |
| lokasi     | Active      | Active      | Active     |
| point      | Coming Soon | Coming Soon | Active     |
| redeem     | Coming Soon | Coming Soon | Active     |
| statistik  | No Access   | Active      | Active     |
| laporan    | No Access   | Active      | Active     |
| admin      | No Access   | No Access   | Active     |

### General Interaction

| Input Type | Description | Bot Response |
|------------|-------------|---------------|
| **Text Message** | General questions about waste | AI-powered response with guidance |
| **Image** | Photo of waste item | Automatic classification and disposal instructions |
| **Location** | Share location | Nearest collection points and schedule |

### Response Examples

**Registration Flow:**
```
User: daftar
Bot: Silakan masukkan nama lengkap Anda:
User: John Doe
Bot: Sekarang masukkan alamat lengkap Anda:
User: Jl. Merdeka No. 123, Jakarta
Bot: Registrasi berhasil! Anda terdaftar sebagai warga.
```

**Waste Classification:**
```
User: [sends image of plastic bottle]
Bot: Sampah terdeteksi: Plastik (PET)
Cara daur ulang: Kumpulkan di tempat sampah biru
Lokasi TPS terdekat: TPS Jalan Mawar (0.5 km)
Jadwal pengambilan: Senin, Rabu, Jumat - 08:00
```

## License

Licensed under the Apache License, Version 2.0. See the LICENSE file for details.

## Support

For technical support or questions about the EcoBot system, please contact the development team or open an issue on the project repository.
