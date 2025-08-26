# EcoBot

Backend for WhatsApp-based waste management with AI assistance and role-based features.

## Overview

EcoBot is a Flask backend that integrates WhatsApp messaging, AI text/image services, and a SQLite database to provide education, schedules, locations, and admin operations. The bot supports three AI modes and long‑term conversation memory stored in the database.

## Features

- AI chat with conversation memory (database backed)
- Image analysis for waste classification
- Role-based commands: warga, koordinator, admin
- Collection points and schedules from the database
- Admin command suite over WhatsApp
- Configurable registration flow (auto or manual)

## Tech Stack

- Python 3.10+, Flask
- SQLite
- [WAHA for WhatsApp integration](https://waha.devlike.pro/)
- AI providers: [Lunos.tech](https://lunos.tech/) (text), [Unli.dev](https://unli.dev/) (vision)
- Mail Service: [Mailry.co](https://mailry.co/)

## Setup

Requirements: Python 3.10+, pip, virtualenv, API keys for WAHA/Lunos/Mailry.

```bash
git clone https://github.com/mycoderisyad/raflangt-ecobot.git
cd raflangt-ecobot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your keys
```

### Key environment variables

- WAHA_BASE_URL, WAHA_API_KEY, WAHA_SESSION_NAME, WEBHOOK_URL
- LUNOS_API_KEY, LUNOS_BASE_URL, LUNOS_TEXT_MODEL, LUNOS_VISION_MODEL
- MAILRY_API_KEY, MAILRY_BASE_URL, MAILRY_FROM_EMAIL, MAILRY_TO_EMAIL
- GOOGLE_MAPS_API_KEY
- REGISTRATION_MODE=auto|manual (default: auto)

## Run

```bash
python3 main.py              # development
python3 main.py --production # production
```

## AI Modes

- /layanan-ecobot: EcoBot Service (database only)
- /general-ecobot: General Waste Management
- /hybrid-ecobot: Hybrid (default)

## Commands by role

Warga:
- edukasi, jadwal, lokasi, help

Koordinator:
- Semua perintah warga + statistik, laporan

Admin:
- Semua perintah koordinator + point, redeem, /admin (user and point management, stats, logs, backup, broadcast, report, memory_stats)

## Registration

Auto registration is enabled by default. To require manual registration, set REGISTRATION_MODE=manual. When manual mode is on, the bot collects name and address in free form and normalizes them via AI/utils before storing.

## Database

SQLite file path can be set via DATABASE_PATH. Tables include users, collection_points, collection_schedules, waste_classifications, user_memory, conversation_history, user_interactions, system_logs.

## Endpoints

- GET /           – health/info
- GET /health     – system health
- POST /webhook   – WhatsApp webhook

## License

Apache 2.0. See LICENSE.
