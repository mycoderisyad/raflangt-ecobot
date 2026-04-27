# EcoBot — API Reference

## Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info |
| GET | `/health` | System health check |

### Webhooks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook/whatsapp` | WhatsApp (WAHA) webhook |
| POST | `/webhook/telegram` | Telegram Bot API webhook |

### Users (Admin)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/users` | List users |
| GET | `/api/users/<phone>` | Get user details |

---

## WhatsApp Webhook Payload (from WAHA)

```json
{
  "event": "message",
  "session": "default",
  "payload": {
    "from": "6281234567890@c.us",
    "body": "user message text",
    "hasMedia": false,
    "type": "chat"
  }
}
```

Image message:
```json
{
  "event": "message",
  "session": "default",
  "payload": {
    "from": "6281234567890@c.us",
    "body": "",
    "hasMedia": true,
    "type": "image",
    "mediaUrl": "https://waha.example.com/api/media/..."
  }
}
```

## Telegram Webhook Payload

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456789,
      "first_name": "User",
      "username": "username"
    },
    "chat": {
      "id": 123456789,
      "type": "private"
    },
    "text": "user message text"
  }
}
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_PROVIDER` | AI provider to use | `gemini` or `openai` |
| `AI_API_KEY` | API key for chosen provider | `sk-...` or `AIza...` |
| `AI_MODEL` | Model name | `gemini-2.0-flash` / `gpt-4o-mini` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/ecobot` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_BASE_URL` | Override AI API base URL | Auto-detected from provider |
| `WHATSAPP_ENABLED` | Enable WhatsApp channel | `true` |
| `WAHA_BASE_URL` | WAHA API base URL | — |
| `WAHA_API_KEY` | WAHA API key | — |
| `WAHA_SESSION_NAME` | WAHA session name | `default` |
| `TELEGRAM_ENABLED` | Enable Telegram channel | `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — |
| `RESEND_API_KEY` | Resend email API key | — |
| `EMAIL_FROM` | Sender email address | — |
| `EMAIL_TO` | Default recipient email | — |
| `VILLAGE_NAME` | Village/area name | — |
| `VILLAGE_COORDINATES` | GPS coordinates | — |
| `ADMIN_PHONE_NUMBERS` | Comma-separated admin phones | — |
| `COORDINATOR_PHONE_NUMBERS` | Comma-separated coordinator phones | — |
| `REGISTRATION_MODE` | `auto` or `manual` | `auto` |
| `ENVIRONMENT` | `development` or `production` | `development` |
| `PORT` | Server port | `5000` (dev) / `8000` (prod) |
| `ADMIN_PANEL_SECRET_KEY` | Flask session secret | — |
| `ADMIN_PANEL_USERNAME` | Admin panel login | `admin` |
| `ADMIN_PANEL_PASSWORD` | Admin panel password | — |
