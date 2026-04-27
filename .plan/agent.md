# EcoBot — Agent Architecture

## Overview

EcoBot menggunakan LLM sebagai brain utama untuk memahami intent user dan menghasilkan respons natural. Tidak ada command parsing berbasis regex — semua routing dilakukan oleh LLM.

## Provider Strategy

- **Single SDK**: Semua provider diakses via `openai` Python SDK (OpenAI-compatible API)
- **Switchable**: Provider dipilih via `AI_PROVIDER` env var (`gemini` atau `openai`)
- **Multimodal**: Kedua provider support text + image dalam satu chat completion call
- **Base URLs**:
  - Gemini: `https://generativelanguage.googleapis.com/v1beta/openai/`
  - OpenAI: `https://api.openai.com/v1/`

## Agent Flow

```
User Message → Channel (WA/Telegram)
    → Webhook API
    → Orchestrator
    → Intent Resolver (lightweight LLM call)
    → Route to handler:
        ├── General Chat → AI Agent (full context)
        ├── Image Analysis → AI Agent (multimodal)
        ├── Schedule Query → DB fetch + AI format
        ├── Location Query → DB fetch + AI format
        ├── Education → AI generate from knowledge
        ├── Statistics → DB fetch + AI format (role-gated)
        ├── Report → Generate PDF + email
        └── Admin → Admin handler
    → AI generates natural response
    → Channel sends response
```

## Intent Resolution

Intent resolver menggunakan lightweight LLM call dengan classification prompt:
- Input: user message + recent conversation history
- Output: structured JSON `{"intent": "...", "params": {...}}`
- Intents: `chat`, `image_analysis`, `schedule`, `location`, `education`, `statistics`, `report`, `admin`, `registration`, `help`, `greeting`
- Fallback: `chat` (general conversation)

## Memory Management

- **Conversation history**: Disimpan di PostgreSQL per-user
- **Context window**: Last N messages (configurable, default 20)
- **User facts**: Key facts extracted from conversation (nama, preferensi, dll)
- **Session**: Tidak ada session timeout — conversation is continuous

## Prompt Composition

System prompt dibangun secara modular:
1. **Base prompt** (`base.md`) — Identity, personality, general rules
2. **Feature prompt** — Specific instructions per intent (waste_expert.md, image_analysis.md, etc.)
3. **Dynamic context** — User data, available schedules, collection points dari DB
4. **User history summary** — Recent conversation summary

## Role-Based Access

| Feature | Warga | Koordinator | Admin |
|---------|-------|-------------|-------|
| Chat / Education | ✅ | ✅ | ✅ |
| Schedule / Location | ✅ | ✅ | ✅ |
| Image Analysis | ✅ | ✅ | ✅ |
| Statistics | ❌ | ✅ | ✅ |
| Reports (email) | ❌ | ✅ | ✅ |
| User Management | ❌ | ❌ | ✅ |
| System Admin | ❌ | ❌ | ✅ |
