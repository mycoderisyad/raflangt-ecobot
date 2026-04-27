# EcoBot v2 — Waste Management Assistant

A modular Python/Flask backend for waste management via **WhatsApp** and **Telegram**. Powered by **Gemini** or **OpenAI** (selectable at runtime), backed by **PostgreSQL**, with role-based workflows, AI vision for waste classification, and automated email reports via **Resend**.

## Architecture

```
src/
├── ai/           # AI provider, agent, prompt templates
├── api/          # Flask blueprints (webhooks, users, health)
├── channels/     # WhatsApp (WAHA) + Telegram abstraction
├── core/         # Orchestrator, intent resolver, constants
├── database/     # PostgreSQL pool, migrations, models
├── services/     # Email (Resend), reports (PDF), registration
├── utils/        # Logger, phone, formatting helpers
├── config.py     # Centralised settings from env vars
└── app.py        # Flask application factory
```

## Features

- **Dual AI Provider** — Gemini multimodal or OpenAI via a single OpenAI-compatible SDK
- **Multi-Channel** — WhatsApp (WAHA) + Telegram Bot API
- **Natural Language** — No slash commands required; LLM-based intent resolution
- **AI Vision** — Send a photo → waste classification + recycling tips
- **PostgreSQL** — Conversation history, user memory, waste stats
- **Role-Based Access** — admin / koordinator / warga
- **Modular Prompts** — Markdown templates composed at runtime
- **Email Reports** — PDF generation + delivery via Resend
- **Admin Panel** — Flask templates with extracted CSS
- **Docker-Ready** — `docker compose up` for production

## Quick Start

```bash
git clone https://github.com/mycoderisyad/raflangt-ecobot.git
cd raflangt-ecobot
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env                           # edit with your keys

# First-time database setup (PostgreSQL must be running)
python manage.py db:setup

# Setup webhooks
python manage.py webhook:tg         # register Telegram webhook
python manage.py webhook:wa         # WhatsApp (WAHA) setup guide

# Start dev server (uvicorn with hot reload)
python main.py
```

### Production (Docker)

```bash
cp .env.example .env   # fill in real values
docker compose up -d --build
```

## Management CLI (`manage.py`)

```bash
# Database
python manage.py db:create          # create PostgreSQL database
python manage.py db:migrate         # run migration files
python manage.py db:seed            # insert sample data
python manage.py db:setup           # create + migrate + seed (first time)
python manage.py db:reset           # drop all tables, re-migrate + seed
python manage.py db:status          # show tables and row counts

# Webhooks
python manage.py webhook:tg         # set Telegram webhook URL
python manage.py webhook:tg:info    # check Telegram webhook status
python manage.py webhook:tg:delete  # remove Telegram webhook
python manage.py webhook:wa         # WhatsApp (WAHA) setup guide
```

## Key Environment Variables

| Variable | Description | Default |
|---|---|---|
| `AI_PROVIDER` | `gemini` or `openai` | `gemini` |
| `AI_API_KEY` | API key for chosen provider | — |
| `AI_MODEL` | Model name | `gemini-2.0-flash` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://…/ecobot` |
| `WHATSAPP_ENABLED` | Enable WhatsApp channel | `true` |
| `WAHA_BASE_URL` | WAHA API URL | — |
| `WAHA_API_KEY` | WAHA API key | — |
| `TELEGRAM_ENABLED` | Enable Telegram channel | `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — |
| `RESEND_API_KEY` | Resend email API key | — |
| `ADMIN_PHONE_NUMBERS` | Comma-separated admin phones | — |

See `.env.example` for the full list.

## Webhooks

| Channel | Endpoint |
|---|---|
| WhatsApp (WAHA) | `POST /webhook/whatsapp` |
| Telegram | `POST /webhook/telegram` |
| Health check | `GET /health` |

## Roles & Access

| Role | Capabilities |
|---|---|
| **warga** | Chat, education, schedule, location, image analysis |
| **koordinator** | + statistics, reports |
| **admin** | + full admin panel, user management |

## License

MIT
