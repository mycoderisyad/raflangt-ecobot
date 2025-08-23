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

## Configuration

### Production Configuration

For production deployment, ensure all environment variables are properly configured:

```env
# Production Environment
ENVIRONMENT=production
PORT=8000
DEBUG=false

# Security Configuration (REQUIRED)
SECRET_KEY=your-super-secure-secret-key-here
ADMIN_PANEL_SECRET_KEY=your-admin-panel-secret-key-here
ADMIN_PANEL_USERNAME=admin
ADMIN_PANEL_PASSWORD=your-secure-admin-password

# Service Configuration
AI_ENABLED=true
MAPS_ENABLED=true

# WhatsApp API Configuration
WAHA_BASE_URL=https://your-waha-instance.com/api
WAHA_API_KEY=your_waha_api_key
WAHA_SESSION_NAME=ecobot_production
WEBHOOK_URL=https://your-domain.com/webhook

# AI Services
LUNOS_API_KEY=your_lunos_api_key
LUNOS_BASE_URL=https://api.lunos.tech/v1
UNLI_API_KEY=your_unli_api_key

# Email Service
MAILRY_API_KEY=your_mailry_api_key
MAILRY_BASE_URL=https://api.mailry.co/ext
MAILRY_FROM_EMAIL=noreply@yourdomain.com
MAILRY_TO_EMAIL=admin@yourdomain.com

# Maps Integration
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# User Roles
ADMIN_PHONE_NUMBERS=+6281234567890,+6281234567891
KOORDINATOR_PHONE_NUMBERS=+6281234567892,+6281234567893

# Community Settings
VILLAGE_NAME=Your Village Name
VILLAGE_COORDINATES=-6.2088,106.8456
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
| `laporan` | Generate PDF reports via email | `laporan` |
| `broadcast` | Send broadcast message | `broadcast [message]` |
| `user list` | List registered users | `user list` |
| `/admin report` | Generate comprehensive PDF report | `/admin report` |

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

### Prerequisites

- Ubuntu/CentOS server with root access
- Python 3.10+ installed
- Nginx web server
- SSL certificates for HTTPS
- Domain name configured

### Step-by-Step Deployment

#### 1. Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-venv nginx supervisor -y

# Create application user
sudo useradd -m -s /bin/bash ecobot
sudo mkdir -p /opt/ecobot
sudo chown ecobot:ecobot /opt/ecobot
```

#### 2. Application Installation

```bash
# Switch to application user
sudo su - ecobot

# Clone and setup application
cd /opt/ecobot
git clone https://github.com/mycoderisyad/raflangt-ecobot.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values
nano .env
```

#### 3. Database Initialization

```bash
# Create database directory
mkdir -p database

# Initialize database with schema
sqlite3 database/ecobot.db < database/schema.sql

# Optional: Load sample data
sqlite3 database/ecobot.db < database/dummy_data.sql
```

#### 4. Systemd Service Configuration

```bash
# Create main application service
sudo nano /etc/systemd/system/ecobot.service
```

```ini
[Unit]
Description=EcoBot - Waste Management System
After=network.target

[Service]
Type=simple
User=ecobot
Group=ecobot
WorkingDirectory=/opt/ecobot
Environment=PATH=/opt/ecobot/venv/bin
EnvironmentFile=/opt/ecobot/.env
ExecStart=/opt/ecobot/venv/bin/python main.py --production
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Create admin panel service
sudo nano /etc/systemd/system/ecobot-admin.service
```

```ini
[Unit]
Description=EcoBot Admin Panel
After=network.target

[Service]
Type=simple
User=ecobot
Group=ecobot
WorkingDirectory=/opt/ecobot/admin_panel
Environment=PATH=/opt/ecobot/venv/bin
EnvironmentFile=/opt/ecobot/.env
ExecStart=/opt/ecobot/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable ecobot ecobot-admin
sudo systemctl start ecobot ecobot-admin
```

#### 5. Nginx Configuration

```bash
# Create main application config
sudo nano /etc/nginx/sites-available/ecobot
```

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
    
    # Webhook endpoint with special handling
    location /webhook {
        proxy_pass http://127.0.0.1:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
        client_max_body_size 50M;
    }
}

# Admin panel configuration
server {
    listen 443 ssl http2;
    server_name admin.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Admin panel security
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com admin.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Enable site and reload nginx
sudo ln -s /etc/nginx/sites-available/ecobot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Security Guidelines

### Production Security Checklist

#### Environment Security
- [ ] All API keys stored in environment variables
- [ ] Strong, unique passwords for admin access
- [ ] Secure secret keys generated (minimum 32 characters)
- [ ] Environment variables properly configured
- [ ] Database file permissions restricted (600)

#### Network Security
- [ ] HTTPS/SSL certificates installed and configured
- [ ] Firewall rules configured (only ports 22, 80, 443 open)
- [ ] Rate limiting enabled on API endpoints
- [ ] Webhook endpoints secured with proper authentication
- [ ] Admin panel accessible only via secure subdomain

#### Application Security
- [ ] Debug mode disabled in production
- [ ] Detailed error messages hidden from end users
- [ ] Input validation implemented on all endpoints
- [ ] SQL injection protection through parameterized queries
- [ ] XSS protection headers configured

#### Monitoring and Maintenance
- [ ] Log monitoring system configured
- [ ] Regular security updates scheduled
- [ ] Backup procedures implemented
- [ ] Health checks configured
- [ ] Error alerting system in place

### Security Best Practices

1. **API Key Management**
   - Never commit API keys to version control
   - Rotate API keys regularly
   - Use different keys for development and production
   - Monitor API key usage and implement quotas

2. **Admin Access Control**
   - Use strong passwords (minimum 12 characters)
   - Enable two-factor authentication where possible
   - Limit admin panel access to trusted IP addresses
   - Regular audit of admin access logs

3. **Database Security**
   - Regular database backups
   - Encrypt sensitive data at rest
   - Use prepared statements to prevent SQL injection
   - Monitor database access and unusual activity

4. **Server Hardening**
   - Keep operating system updated
   - Disable unnecessary services
   - Configure proper file permissions
   - Use fail2ban for intrusion prevention

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
