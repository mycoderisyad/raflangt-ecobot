# EcoBot — System Architecture

## Tech Stack

- **Runtime**: Python 3.11+
- **Web Framework**: Flask
- **Database**: PostgreSQL
- **AI**: OpenAI SDK (Gemini + OpenAI via OpenAI-compatible API)
- **Messaging**: WhatsApp (WAHA), Telegram (Bot API)
- **Email**: Resend
- **PDF**: ReportLab
- **Deployment**: Docker + Docker Compose (production), bare Python (development)

## Folder Structure

```
raflangt-ecobot/
├── src/                          # Main application source
│   ├── __init__.py
│   ├── app.py                    # Flask app factory
│   ├── config.py                 # Centralized config (pydantic-style dataclasses)
│   ├── api/                      # HTTP endpoints
│   │   ├── __init__.py           # Blueprint registration
│   │   ├── health.py             # Health check endpoints
│   │   ├── webhook_whatsapp.py   # WhatsApp webhook
│   │   ├── webhook_telegram.py   # Telegram webhook
│   │   └── users.py              # User API (admin)
│   ├── core/                     # Business logic
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Main message processing pipeline
│   │   ├── intent_resolver.py    # LLM-based intent classification
│   │   └── constants.py          # Waste types, roles, feature flags
│   ├── ai/                       # AI layer
│   │   ├── __init__.py
│   │   ├── provider.py           # AI provider factory + client
│   │   ├── agent.py              # Conversation agent (chat + image)
│   │   └── prompts/
│   │       ├── system.py         # Prompt builder
│   │       ├── context.py        # Dynamic context injection
│   │       └── templates/        # .md prompt templates
│   │           ├── base.md
│   │           ├── waste_expert.md
│   │           ├── image_analysis.md
│   │           └── admin.md
│   ├── channels/                 # Messaging channel abstraction
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract channel interface
│   │   ├── whatsapp.py           # WAHA integration
│   │   └── telegram.py           # Telegram Bot API
│   ├── services/                 # External services
│   │   ├── __init__.py
│   │   ├── email.py              # Resend email
│   │   ├── report.py             # PDF report generation
│   │   ├── registration.py       # User registration flow
│   │   └── image.py              # Image encoding/validation
│   ├── database/                 # Data layer
│   │   ├── __init__.py
│   │   ├── connection.py         # PostgreSQL connection pool
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── conversation.py
│   │   │   ├── collection.py
│   │   │   ├── waste.py
│   │   │   └── system.py
│   │   └── migrations/
│   │       └── 001_initial.sql
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── phone.py
│       └── formatting.py
├── admin_panel/                  # Admin web interface
│   ├── app.py
│   ├── static/
│   │   └── css/
│   │       └── admin.css
│   └── templates/
│       ├── base.html
│       └── ...
├── docs/                         # Public documentation
│   ├── index.html
│   └── css/
│       └── docs.css
├── .plan/                        # Design documents
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── main.py                       # Entry point
├── .env.example
├── requirements.txt
└── README.md
```

## Data Flow

```
[WhatsApp/Telegram] → [Webhook API] → [Orchestrator]
                                            │
                                    [Intent Resolver] (LLM)
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                        [AI Agent]    [DB Query]    [Services]
                              │             │             │
                              └─────────────┼─────────────┘
                                            ▼
                                    [AI Format Response]
                                            │
                                    [Channel Send]
                                            │
                                    [WhatsApp/Telegram]
```

## Key Design Principles

1. **Channel-agnostic**: Core logic doesn't know about WA or Telegram specifics
2. **Provider-agnostic**: AI code uses single interface, provider swapped via config
3. **LLM-first routing**: No regex command parsing, LLM understands intent
4. **Natural responses**: All user-facing text generated by LLM, no static templates
5. **Modular prompts**: System prompts composed from template files, not hardcoded
6. **Role-based access**: Features gated by user role at orchestrator level
