# EcoBot

Intelligent waste management backend system for community waste classification, recycling education, and collection coordination through WhatsApp integration.

## Overview

EcoBot is a professional Python Flask-based backend system designed to revolutionize community waste management through intelligent automation and seamless integration with messaging platforms. The system provides automated waste classification, collection coordination, and environmental education initiatives.

## Key Features

- AI-powered waste classification from images
- WhatsApp Business API integration for community access
- Multi-role user management (Admin, Coordinator, Resident)
- Collection point mapping and routing
- Real-time analytics and environmental impact tracking
- Administrative dashboard for system management
- Automated email notifications and reporting

## Architecture

| Component | Technology | Purpose |
|-----------|------------|----------|
| **Backend Framework** | Flask + Python 3.10+ | REST API and business logic |
| **Database** | SQLite | User data and application state |
| **WhatsApp API** | WAHA Integration | Message handling and webhook processing |
| **AI Services** | [Lunos.tech](https://lunos.tech/) & [Unli.dev](https://unli.dev/) | Waste classification and NLP |
| **Email Service** | [Mailry.co](https://mailry.co/) | Automated notifications |
| **Web Server** | Gunicorn + Nginx | Production deployment |
| **Admin Panel** | Flask + Jinja2 | Web-based administration interface |

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

## Configuration

### Required Environment Variables

```env
# Application Environment
ENVIRONMENT=development
PORT=8000

# WhatsApp HTTP API (WAHA)
WAHA_BASE_URL=https://your-waha-instance.com/api
WAHA_API_KEY=your_waha_api_key
WAHA_SESSION_NAME=default

# AI Classification Services
LUNOS_API_KEY=your_lunos_api_key
LUNOS_BASE_URL=https://api.lunos.tech/v1

# Email Notification Service
MAILRY_API_KEY=your_mailry_api_key
MAILRY_BASE_URL=https://api.mailry.co/ext

# Admin Panel Configuration
ADMIN_PANEL_USERNAME=admin
ADMIN_PANEL_PASSWORD=secure_password
ADMIN_PANEL_SECRET_KEY=your_secret_key
ADMIN_PHONE_NUMBERS=+6281234567890,+6281234567891

# Database Configuration
DATABASE_PATH=database/ecobot.db
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

| Endpoint | Method | Description |
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

### User Registration Commands

| Command | Description | Example |
|---------|-------------|----------|
| `daftar` | Start user registration process | `daftar` |
| `register` | Alternative registration command | `register` |

### Information Commands

| Command | Description | Example |
|---------|-------------|----------|
| `info` | Get general information about EcoBot | `info` |
| `help` | Show available commands and help | `help` |
| `bantuan` | Show help in Indonesian | `bantuan` |
| `jadwal` | Get waste collection schedule | `jadwal` |
| `lokasi` | Find nearest collection points | `lokasi` |
| `tps` | Find nearest TPS (Tempat Pembuangan Sementara) | `tps` |

### Waste Classification Commands

| Command | Description | Example |
|---------|-------------|----------|
| Send image | Upload waste image for classification | *[Send photo]* |
| `klasifikasi` | Request waste classification help | `klasifikasi` |
| `jenis sampah` | Learn about waste types | `jenis sampah` |
| `cara buang` | Get disposal instructions | `cara buang plastik` |

### Points and Rewards Commands

| Command | Description | Example |
|---------|-------------|----------|
| `poin` | Check current points balance | `poin` |
| `point` | Alternative points check command | `point` |
| `saldo` | Check points balance | `saldo` |
| `riwayat` | View points history | `riwayat` |

### Educational Commands

| Command | Description | Example |
|---------|-------------|----------|
| `edukasi` | Get environmental education content | `edukasi` |
| `tips` | Get waste management tips | `tips` |
| `daur ulang` | Learn about recycling | `daur ulang` |
| `lingkungan` | Environmental facts and tips | `lingkungan` |

### Status and Profile Commands

| Command | Description | Example |
|---------|-------------|----------|
| `profil` | View user profile information | `profil` |
| `status` | Check account status | `status` |
| `statistik` | View personal waste management stats | `statistik` |

### Admin Commands (Coordinators and Admins only)

| Command | Description | Example |
|---------|-------------|----------|
| `admin` | Access admin functions | `admin` |
| `laporan` | Generate reports | `laporan` |
| `broadcast` | Send broadcast message | `broadcast [message]` |
| `user list` | List registered users | `user list` |

### General Interaction

| Input Type | Description | Bot Response |
|------------|-------------|---------------|
| **Text Message** | General questions about waste | AI-powered response with guidance |
| **Image** | Photo of waste item | Automatic classification and disposal instructions |
| **Location** | Share location | Nearest collection points and schedule |
| **Contact** | Share contact | Add to user profile for notifications |

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

**Points Check:**
```
User: poin
Bot: Saldo poin Anda: 150 poin
Total sampah yang sudah didaur ulang: 25 item
Level: Bronze Recycler
```

## Command Reference

### Development Commands

| Command | Description |
|---------|-------------|
| `python3 main.py` | Start application in development mode |
| `python3 main.py --production` | Start application in production mode |
| `pip install -r requirements.txt` | Install project dependencies |
| `python3 -m venv venv` | Create virtual environment |
| `source venv/bin/activate` | Activate virtual environment (Linux/Mac) |
| `venv\Scripts\activate` | Activate virtual environment (Windows) |
| `deactivate` | Deactivate virtual environment |

### Production Commands

| Command | Description |
|---------|-------------|
| `gunicorn -w 4 -b 0.0.0.0:8000 'main:create_app("production")'` | Start with Gunicorn (4 workers) |
| `sudo systemctl start ecobot` | Start EcoBot service |
| `sudo systemctl stop ecobot` | Stop EcoBot service |
| `sudo systemctl restart ecobot` | Restart EcoBot service |
| `sudo systemctl status ecobot` | Check EcoBot service status |
| `sudo systemctl enable ecobot` | Enable EcoBot service on boot |
| `sudo systemctl disable ecobot` | Disable EcoBot service on boot |

### Admin Panel Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start ecobot-admin` | Start admin panel service |
| `sudo systemctl stop ecobot-admin` | Stop admin panel service |
| `sudo systemctl restart ecobot-admin` | Restart admin panel service |
| `sudo systemctl status ecobot-admin` | Check admin panel service status |

### Database Commands

| Command | Description |
|---------|-------------|
| `sqlite3 database/ecobot.db` | Access SQLite database directly |
| `sqlite3 database/ecobot.db ".tables"` | List all database tables |
| `sqlite3 database/ecobot.db ".schema"` | Show database schema |
| `sqlite3 database/ecobot.db "SELECT * FROM users;"` | Query users table |

### Log and Monitoring Commands

| Command | Description |
|---------|-------------|
| `sudo journalctl -u ecobot -f` | Follow EcoBot service logs |
| `sudo journalctl -u ecobot-admin -f` | Follow admin panel service logs |
| `tail -f logs/ecobot.log` | Follow application logs (if file logging enabled) |
| `curl http://localhost:8000/health` | Check application health status |
| `curl https://yourdomain.com/health` | Check production health status |

### Nginx Commands

| Command | Description |
|---------|-------------|
| `sudo nginx -t` | Test Nginx configuration |
| `sudo systemctl reload nginx` | Reload Nginx configuration |
| `sudo systemctl restart nginx` | Restart Nginx service |
| `sudo systemctl status nginx` | Check Nginx service status |

## Production Deployment

### Systemd Service Setup

```bash
# Create systemd service file
sudo nano /etc/systemd/system/ecobot.service

# Add service configuration
[Unit]
Description=EcoBot - Waste Management Assistant
After=network.target

[Service]
Type=simple
User=ecobot
WorkingDirectory=/opt/ecobot
Environment=PATH=/opt/ecobot/venv/bin
ExecStart=/opt/ecobot/venv/bin/python main.py --production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ecobot
sudo systemctl start ecobot
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name ecobot.yourdomain.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Admin Panel Setup

```bash
# Setup admin panel service
sudo systemctl enable ecobot-admin
sudo systemctl start ecobot-admin

# Access admin panel
# https://panel.yourdomain.com
```

## Security Considerations

- Store API keys in environment variables, never in source code
- Use HTTPS/SSL encryption for all production deployments
- Implement proper firewall rules and access controls
- Regularly update dependencies and monitor for security vulnerabilities
- Use strong passwords for admin panel access
- Enable rate limiting on webhook endpoints

## Contributing

When contributing to this project, please follow these guidelines:

1. Maintain the minimalist, Notion-inspired design aesthetic
2. Follow Python PEP 8 coding standards
3. Ensure all forms maintain UI consistency
4. Test changes thoroughly before submission
5. Update documentation as needed

## License

Licensed under the Apache License, Version 2.0. See the LICENSE file for details.

## Support

For technical support or questions about the EcoBot system, please contact the development team or open an issue on the project repository.
