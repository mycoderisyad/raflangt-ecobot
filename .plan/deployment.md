# EcoBot Local Runtime

## Prerequisites

- Python 3.12+
- PostgreSQL running locally with the database in `DATABASE_URL`
- Telegram bot token for bot checks and message tests
- AI provider API key for AI responses and photo classification

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py db:setup
python manage.py telegram:check
python main.py
```

For an existing populated database, use `python manage.py db:migrate`. Migrations are tracked in `schema_migrations`; the CLI never drops data. Run `python manage.py db:seed` when sample collection points and schedules are wanted. Re-running seed does not duplicate the included sample schedules.

## Telegram modes

### Polling for local testing

Set `TELEGRAM_ENABLED=true` and `TELEGRAM_MODE=polling`. If the bot currently has a webhook, inspect it with `python manage.py telegram:webhook:info`; switch modes intentionally with `python manage.py telegram:webhook:delete`. Start one API process with `python main.py`, then message the bot in a private chat.

### Webhook

Use an HTTPS URL that forwards to this API. Set `TELEGRAM_MODE=webhook`, configure `TELEGRAM_WEBHOOK_SECRET`, then:

```powershell
python manage.py telegram:webhook:set https://public-domain.example
python main.py
```

Webhook requests use `POST /webhook/telegram` and the `X-Telegram-Bot-Api-Secret-Token` header. Use `telegram:webhook:info` to inspect the current registration and `telegram:webhook:delete` before switching to polling.

## Admin UI client

The API runs at `PORT` (default 8000). OpenAPI is available at `/docs`. Configure `CORS_ORIGINS` with the exact frontend origins. The default development origins are Vite on `localhost:5173` and `127.0.0.1:5173`.

The UI obtains a JWT from `POST /api/v1/auth/login` and sends it as a bearer token. Production requires a random `API_SECRET_KEY` of at least 32 characters and a strong `ADMIN_PASSWORD`. Do not expose `.env` or put bot/API secrets in the frontend.
