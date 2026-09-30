# EcoBot — Backend Architecture

## Overview

EcoBot is a FastAPI backend. Telegram delivers user messages through a webhook or long polling. The shared orchestrator resolves intents, queries PostgreSQL, calls the AI provider when needed, and sends replies with the Telegram Bot API. Admin UI is a separate future client that consumes `/api/v1` JSON endpoints.

## Components

```text
Telegram webhook / polling
          ↓
FastAPI routes → Telegram update processor → Orchestrator → AI Agent
          ↓                                       ↓
     Admin services                          PostgreSQL
          ↓
   Telegram broadcast / Resend PDF reports
```

| Layer | Location | Responsibility |
|---|---|---|
| HTTP application | `src/app.py`, `src/api/` | Lifespan, CORS, validation, authentication, health, admin, Telegram webhook |
| Telegram | `src/channels/telegram.py`, `src/services/telegram_polling.py` | Bot API, message/photo parsing, webhook or polling |
| Message workflow | `src/core/` | Rate limits, intent routing, role access, context |
| AI | `src/ai/` | Gemini/OpenAI provider, prompts, text and image analysis |
| Persistence | `src/database/` | PostgreSQL pool, models, numbered migrations |
| Operations | `src/services/` | Admin data, email/PDF reports, reminders, registration |

## Runtime behavior

- HTTP routes that use synchronous `psycopg2` and `requests` are synchronous FastAPI operations.
- FastAPI lifespan opens the database pool, starts the reminder scheduler and optional Telegram poller, then stops workers and closes the pool.
- `TELEGRAM_MODE=polling` and `TELEGRAM_MODE=webhook` are exclusive for each bot. Polling refuses to start if Telegram still has a webhook registered.
- Run one Uvicorn worker while polling or the reminder scheduler is enabled to avoid duplicate workers.
- Database schema changes run through `manage.py db:migrate`, not application startup.

## Data compatibility

The existing PostgreSQL tables and references remain. User chat identifiers remain in `users.phone_number` internally and are named `user_id` in the public API. Migration 003 adds schedule notes and Telegram update deduplication while retaining existing records.
