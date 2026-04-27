# EcoBot — Deployment Guide

## Development (No Docker)

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (local or remote)
- pip / virtualenv

### Setup
```bash
git clone https://github.com/mycoderisyad/raflangt-ecobot.git
cd raflangt-ecobot
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your configuration

python main.py
```

### Local PostgreSQL
```bash
# Create database
createdb ecobot

# Or via psql
psql -U postgres -c "CREATE DATABASE ecobot;"

# Run migrations
psql -U postgres -d ecobot -f src/database/migrations/001_initial.sql
```

---

## Production (Docker)

### Prerequisites
- Docker
- Docker Compose

### Deploy
```bash
cp .env.example .env
# Edit .env with production values

docker compose -f docker/docker-compose.yml up -d
```

### Docker Compose Services
- **app**: EcoBot Flask application (gunicorn)
- **db**: PostgreSQL 15

### Ports
- App: `8000` (configurable via PORT)
- PostgreSQL: `5432` (internal only)

---

## Environment Checklist

Before deploying, ensure these are configured:

- [ ] `AI_PROVIDER` and `AI_API_KEY` — AI service
- [ ] `DATABASE_URL` — PostgreSQL connection
- [ ] At least one channel enabled:
  - [ ] `WHATSAPP_ENABLED=true` + WAHA config, OR
  - [ ] `TELEGRAM_ENABLED=true` + `TELEGRAM_BOT_TOKEN`
- [ ] `RESEND_API_KEY` — if email reports needed
- [ ] `ADMIN_PANEL_SECRET_KEY` — secure random string
- [ ] `ADMIN_PANEL_PASSWORD` — not the default

---

## Webhook Setup

### WhatsApp (WAHA)
Configure WAHA to send webhooks to:
```
POST https://your-domain.com/webhook/whatsapp
```

### Telegram
Set webhook via Telegram Bot API:
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/webhook/telegram"
```
