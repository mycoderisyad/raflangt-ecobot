# EcoBot - Waste Management Assistant

Professional microservice-based WhatsApp bot for waste management, recycling education, and community coordination.

## 🏗️ Architecture

### Microservice Structure
```
ecobot/
├── core/                   # Core application infrastructure
│   ├── config.py          # Environment-based configuration
│   ├── constants.py       # Clean constants without hardcoded emojis
│   ├── utils.py           # Utility functions and logging
│   └── application_handler.py  # Main application logic
├── services/              # Business logic microservices
│   ├── whatsapp_service.py     # WhatsApp communication
│   ├── ai_service.py           # AI classification (prod/dev modes)
│   ├── message_service.py      # Message formatting
│   └── registration_service.py # User registration
├── environments/          # Environment-specific configurations
│   ├── development/       # Development with AI simulation
│   └── production/        # Production with real APIs
├── messages/              # JSON message templates
├── database/              # Database models and management
└── utils/                 # Legacy utilities (being phased out)
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode (default)
python3 main.py

# Run in production mode
python3 main.py --production
```

## 🎯 Simple Usage

- **Development**: `python3 main.py` (AI simulation, debug enabled)
- **Production**: `python3 main.py --production` (real APIs required)

## 🔧 Configuration

### Single Environment File
EcoBot uses a single `.env` file in the root directory for all configurations:

```env
# Change this to switch environments
ENVIRONMENT=development  # or 'production'

# Your API configurations here...
```

### Environment Modes
- **Development**: AI simulation, debug enabled, no API keys required
- **Production**: Real APIs, optimized performance, API keys required

## 🎯 Features

### Multi-Role System
- **Admin**: Full system access, user management
- **Koordinator**: Waste collection coordination
- **Warga**: Basic waste classification and education

### User Registration
- Required registration with "daftar" command
- Name and address collection
- Role assignment by administrators

### AI Integration
- Waste classification from images
- Smart conversation handling
- Development simulation mode

### WhatsApp Integration
- WAHA API compatibility
- Message formatting and templates
- Phone number normalization

## 📱 Usage Examples

### User Registration
```
User: daftar
Bot: Silakan masukkan nama lengkap Anda:
User: John Doe
Bot: Terima kasih! Sekarang masukkan alamat lengkap Anda:
User: Jl. Merdeka No. 123
Bot: Registrasi berhasil! Anda terdaftar sebagai warga.
```

### Waste Classification
```
User: [sends image of plastic bottle]
Bot: Sampah terdeteksi: Plastik
     Cara daur ulang: [recycling instructions]
```

## 🔐 Environment Variables

### Required for Production
```env
# Set environment to production
ENVIRONMENT=production

# WhatsApp API
WAHA_BASE_URL=https://your-waha-instance.com
WAHA_API_KEY=your_api_key

# AI Service
LUNOS_API_KEY=your_ai_api_key
LUNOS_BASE_URL=https://api.lunos.tech/v1

# Admin Access
ADMIN_PHONE_NUMBERS=+6281234567890,+6287654321098
```

### For Development
```env
# Default development mode
ENVIRONMENT=development

# APIs are optional - simulation will be used
```

## � Domain Setup

### Webhook URL Configuration
```env
# Development (local)
WEBHOOK_URL=http://localhost:5005/webhook

# Production (with domain + SSL)
WEBHOOK_URL=https://ecobot.rafgt.my.id/webhook
```

### SSL Setup for Production
```bash
# Run setup script to configure domain + SSL
sudo bash setup_domain.sh
```

This will:
- Configure Nginx reverse proxy
- Setup SSL certificate with Let's Encrypt
- Enable HTTPS for secure webhook communication

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:5005/

# Expected response:
{
    "status": "healthy",
    "service": "EcoBot",
    "version": "2.0.0",
    "environment": "development"
}
```

## 📚 API Documentation

### Webhook Endpoint
- **URL**: `/webhook`
- **Method**: `POST`
- **Purpose**: Receives WhatsApp messages from WAHA

### Health Check
- **URL**: `/`
- **Method**: `GET`
- **Purpose**: Service health monitoring

## 🔄 Migration from Legacy

The new microservice architecture maintains compatibility with legacy code while providing:
- Clean separation of concerns
- Environment-based configuration
- Professional deployment options
- Reduced code duplication
- Better error handling

## 🛠️ Development

### Adding New Features
1. Create service in `services/` directory
2. Add configuration to `core/config.py`
3. Register with `ApplicationHandler`
4. Update message templates if needed

### Environment Setup
- Use `development` for local testing
- Use `production` for deployment
- All configurations managed through environment files

## 📝 License

Professional waste management solution for community use.
