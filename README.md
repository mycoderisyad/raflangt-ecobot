# EcoBot - AI-Powered Waste Management Assistant

WhatsApp-based AI assistant for rural waste management with intelligent image classification, educational content, and location services.

## Features

- **AI Waste Classification** - Photo analysis using Lunos.tech API
- **Multi-Role System** - Warga, Koordinator, Admin with different access levels
- **WhatsApp Integration** - Twilio Business API for messaging
- **Educational Content** - Waste management tips and guides
- **Location Services** - Google Maps
- **Email Reports** - Professional analytics via Mailry API

## Commands
- `edukasi` - Waste management tips
- `jadwal` - Collection schedules
- `lokasi` - Collection points with maps
- `statistik` - System data (coordinator+)
- `laporan` - Email reports (coordinator+)

## Quick Start

**Prerequisites:** Python 3.8+, Twilio account

1. **Install & Configure**
   ```bash
   git clone <repository-url>
   cd HACKTON
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Environment Variables**
   ```bash
   # Required
   TWILIO_ACCOUNT_SID=
   TWILIO_AUTH_TOKEN=
   TWILIO_WHATSAPP_NUMBER=
   
   # AI Service (recommended)
   LUNOS_API_KEY=your_lunos_api_key
   LUNOS_TEXT_MODEL=openai/gpt-4o-mini
   LUNOS_VISION_MODEL=openai/gpt-4o
   
   # Optional (uses mock if not provided)
   GOOGLE_MAPS_API_KEY=your_google_maps_key
   MAILRY_API_KEY=your_mailry_key
   ```

3. **Start Application**
   ```bash
   python start.py
   
   # Setup webhook (development)
   ngrok http 5001
   # Set Twilio webhook: https://your-ngrok-url.ngrok-free.app/webhook
   ```

## AI Integration

**Lunos.tech** (Unified AI Gateway)
- Supports multiple providers: OpenAI, Anthropic, Google, Meta
- Image analysis for waste classification
- Natural conversation in Bahasa Indonesia

**Recommended Models:**
- Text: `openai/gpt-4o-mini` (cost-effective)
- Vision: `openai/gpt-4o` (best quality)

**Image Support:** JPEG, PNG, WebP (16MB max, WhatsApp compatible)


**VS Code Tasks Available:**
- Run EcoBot (auto-reload)
- Run Tests
- Format Code

## Security & Production

- All API keys in environment variables
- Mock services for development
- Comprehensive fallback mechanisms
- Professional email templates
- Multi-role access control

**Production Checklist:**
- Configure production API keys
- Use WSGI server (Gunicorn)
- Set up reverse proxy (Nginx)
- Enable HTTPS
- Configure monitoring

---

**Note:** Application works in development mode without external API keys using mock services.