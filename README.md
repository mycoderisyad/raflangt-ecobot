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
| **AI Services** | Lunos.tech & Unli.dev | Waste classification and NLP |
| **Email Service** | Mailry.co | Automated notifications |
| **Web Server** | Gunicorn + Nginx | Production deployment |
| **Admin Panel** | Flask + Jinja2 | Web-based administration interface |

## Getting Started

### Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)
- Valid API keys for WAHA, Lunos.tech, and Mailry.co services

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
