"""
Centralized Configuration Management
All settings loaded from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class DatabaseConfig:
    url: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            url=os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/ecobot",
            ),
        )


@dataclass
class AIConfig:
    provider: str = "gemini"
    api_key: str = ""
    model: str = "gemini-2.0-flash"
    base_url: str = ""

    @classmethod
    def from_env(cls) -> "AIConfig":
        provider = os.getenv("AI_PROVIDER", "gemini").lower()
        base_url = os.getenv("AI_BASE_URL", "")
        if not base_url:
            if provider == "gemini":
                base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            else:
                base_url = "https://api.openai.com/v1/"
        return cls(
            provider=provider,
            api_key=os.getenv("AI_API_KEY", ""),
            model=os.getenv("AI_MODEL", "gemini-2.0-flash" if provider == "gemini" else "gpt-4o-mini"),
            base_url=base_url,
        )


@dataclass
class WhatsAppConfig:
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    session_name: str = "default"

    @classmethod
    def from_env(cls) -> "WhatsAppConfig":
        return cls(
            enabled=os.getenv("WHATSAPP_ENABLED", "true").lower() == "true",
            base_url=os.getenv("WAHA_BASE_URL", ""),
            api_key=os.getenv("WAHA_API_KEY", ""),
            session_name=os.getenv("WAHA_SESSION_NAME", "default"),
        )


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        return cls(
            enabled=os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        )


@dataclass
class EmailConfig:
    resend_api_key: str = ""
    from_email: str = ""
    to_email: str = ""

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            resend_api_key=os.getenv("RESEND_API_KEY", ""),
            from_email=os.getenv("EMAIL_FROM", ""),
            to_email=os.getenv("EMAIL_TO", ""),
        )


@dataclass
class AppConfig:
    name: str = "EcoBot"
    version: str = "2.0.0"
    environment: str = "development"
    debug: bool = True
    port: int = 5000
    timezone: str = "Asia/Jakarta"
    village_name: str = ""
    village_coordinates: str = ""
    admin_phones: List[str] = field(default_factory=list)
    coordinator_phones: List[str] = field(default_factory=list)
    admin_telegram_usernames: List[str] = field(default_factory=list)
    coordinator_telegram_usernames: List[str] = field(default_factory=list)
    registration_mode: str = "auto"

    @classmethod
    def from_env(cls) -> "AppConfig":
        env = os.getenv("ENVIRONMENT", "development")
        return cls(
            name=os.getenv("APP_NAME", "EcoBot"),
            version=os.getenv("APP_VERSION", "2.0.0"),
            environment=env,
            debug=env == "development",
            port=int(os.getenv("PORT", "5000" if env == "development" else "8000")),
            timezone=os.getenv("TIMEZONE", "Asia/Jakarta"),
            village_name=os.getenv("VILLAGE_NAME", ""),
            village_coordinates=os.getenv("VILLAGE_COORDINATES", ""),
            admin_phones=_parse_list(os.getenv("ADMIN_PHONE_NUMBERS", "")),
            coordinator_phones=_parse_list(os.getenv("COORDINATOR_PHONE_NUMBERS", "")),
            admin_telegram_usernames=_parse_list(os.getenv("ADMIN_TELEGRAM_USERNAMES", ""), lower=True),
            coordinator_telegram_usernames=_parse_list(os.getenv("COORDINATOR_TELEGRAM_USERNAMES", ""), lower=True),
            registration_mode=os.getenv("REGISTRATION_MODE", "auto").lower(),
        )


@dataclass
class Settings:
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    whatsapp: WhatsAppConfig = field(default_factory=WhatsAppConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app=AppConfig.from_env(),
            database=DatabaseConfig.from_env(),
            ai=AIConfig.from_env(),
            whatsapp=WhatsAppConfig.from_env(),
            telegram=TelegramConfig.from_env(),
            email=EmailConfig.from_env(),
        )


def _parse_list(csv_string: str, *, lower: bool = False) -> List[str]:
    if not csv_string:
        return []
    items = [v.strip().lstrip("@") for v in csv_string.split(",") if v.strip()]
    return [i.lower() for i in items] if lower else items


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_settings: Settings | None = None


def init_settings() -> Settings:
    global _settings
    _settings = Settings.from_env()
    return _settings


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
