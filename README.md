# EcoBot - Intelligent Waste Management Assistant

A professional WhatsApp bot for waste classification, recycling education, and community waste management coordination.

## Features

- **AI-Powered Waste Classification** - Automatic image analysis and waste categorization
- **WhatsApp Integration** - Seamless communication through WhatsApp Business API
- **Multi-Role System** - Admin, Coordinator, and Resident access levels
- **Location Services** - Waste collection points and routing information
- **Analytics & Reporting** - Usage statistics and environmental impact tracking
- **Multi-Environment** - Development and production configurations

## Technology Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **WhatsApp API** | [WAHA](https://github.com/devlikeapro/waha) | WhatsApp HTTP API for message handling |
| **AI Services** | [Lunos.tech](https://lunos.tech/) & [Unli.dev](https://unli.dev/) | AI image classification and natural language processing |
| **Email Service** | [Mailry.co](https://mailry.co/) | Automated email notifications and reports |
| **Backend** | Flask + Python 3.10+ | Microservice architecture with REST API |
| **Database** | SQLite | Lightweight embedded database |
| **Deployment** | Gunicorn + Nginx | Production-ready web server setup |

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/mycoderisyad/raflangt-ecobot.git
cd raflangt-ecobot/ecobot

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys
```

### Running
```bash
# Development mode
python3 main.py

# Production mode
python3 main.py --production

# Production with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 'main:create_app("production")'
```

## Configuration

### Environment Variables
```env
# Application Mode
ENVIRONMENT=development|production

# WhatsApp API (WAHA)
WAHA_BASE_URL=https://your-waha-instance.com/api
WAHA_API_KEY=your_waha_api_key
WAHA_SESSION_NAME=default

# AI Services
LUNOS_API_KEY=your_lunos_api_key
LUNOS_BASE_URL=https://api.lunos.tech/v1

# Email Service
MAILRY_API_KEY=your_mailry_api_key
MAILRY_BASE_URL=https://api.mailry.co/ext

# Admin Configuration
ADMIN_PHONE_NUMBERS=+6281234567890,+6281234567891
```

## Usage Examples

### User Registration
```
User: daftar
Bot: Silakan masukkan nama lengkap Anda:
User: John Doe  
Bot: Sekarang masukkan alamat lengkap Anda:
User: Jl. Merdeka No. 123
Bot: Registrasi berhasil! Anda terdaftar sebagai warga.
```

### Waste Classification
```
User: [sends image of plastic bottle]
Bot: Sampah terdeteksi: Plastik (PET)
     Cara daur ulang: Kumpulkan di tempat sampah biru
     Lokasi TPS terdekat: [map link]
```

## Deployment

### Using Deployment Script
```bash
# Run deployment preparation
./deploy.sh

# Start production server
python3 main.py --production
```

### Docker (Optional)
```bash
# Build image
docker build -t ecobot .

# Run container
docker run -p 8000:8000 --env-file .env ecobot
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and service status |
| `/webhook` | POST | WhatsApp webhook for incoming messages |

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**EcoBot** - Making waste management smarter, one message at a time.
