"""Centralized configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field


def _parse_list(raw: str, *, lower: bool = False) -> list[str]:
    values = [value.strip().lstrip("@") for value in raw.split(",") if value.strip()]
    return [value.lower() for value in values] if lower else values


@dataclass
class DatabaseConfig:
    url: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            os.getenv(
                "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ecobot"
            )
        )


@dataclass
class AIConfig:
    provider: str = "gemini"
    api_key: str = ""
    model: str = ""
    base_url: str = ""

    @classmethod
    def from_env(cls) -> "AIConfig":
        provider = os.getenv("AI_PROVIDER", "gemini").lower()
        base_url = os.getenv("AI_BASE_URL", "").strip()
        if not base_url:
            base_url = (
                "https://generativelanguage.googleapis.com/v1beta/openai/"
                if provider == "gemini"
                else "https://api.openai.com/v1/"
            )
        return cls(
            provider=provider,
            api_key=os.getenv("AI_API_KEY", ""),
            model=os.getenv(
                "AI_MODEL",
                "gemini-2.0-flash" if provider == "gemini" else "gpt-4o-mini",
            ),
            base_url=base_url,
        )


@dataclass
class WebSearchConfig:
    api_key: str = ""
    daily_limit: int = 30
    user_daily_limit: int = 3

    @classmethod
    def from_env(cls) -> "WebSearchConfig":
        api_key = next(
            (
                value.strip()
                for name in ("BRAVE_SEARCH_API_KEY", "BRAVE_API_KEY")
                if (value := os.getenv(name, "")).strip()
            ),
            "",
        )
        return cls(
            api_key=api_key,
            daily_limit=max(0, int(os.getenv("WEB_SEARCH_DAILY_LIMIT", "30"))),
            user_daily_limit=max(0, int(os.getenv("WEB_SEARCH_USER_DAILY_LIMIT", "3"))),
        )


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""
    webhook_secret: str = ""
    mode: str = "polling"

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        mode = os.getenv("TELEGRAM_MODE", "polling").lower()
        if mode not in {"polling", "webhook"}:
            raise ValueError("TELEGRAM_MODE must be 'polling' or 'webhook'")
        return cls(
            enabled=os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", ""),
            mode=mode,
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
    port: int = 8000
    timezone: str = "Asia/Jakarta"
    village_name: str = ""
    village_coordinates: str = ""
    admin_telegram_usernames: list[str] = field(default_factory=list)
    coordinator_telegram_usernames: list[str] = field(default_factory=list)
    registration_mode: str = "auto"
    api_secret_key: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    cors_origins: list[str] = field(default_factory=list)
    jwt_ttl_seconds: int = 3600

    @classmethod
    def from_env(cls) -> "AppConfig":
        env = os.getenv("ENVIRONMENT", "development")
        default_origins = (
            "http://localhost:5173,http://127.0.0.1:5173"
            if env == "development"
            else ""
        )
        return cls(
            name=os.getenv("APP_NAME", "EcoBot"),
            version=os.getenv("APP_VERSION", "2.0.0"),
            environment=env,
            debug=env == "development",
            port=int(os.getenv("PORT", "8000")),
            timezone=os.getenv("TIMEZONE", "Asia/Jakarta"),
            village_name=os.getenv("VILLAGE_NAME", ""),
            village_coordinates=os.getenv("VILLAGE_COORDINATES", ""),
            admin_telegram_usernames=_parse_list(
                os.getenv("ADMIN_TELEGRAM_USERNAMES", ""), lower=True
            ),
            coordinator_telegram_usernames=_parse_list(
                os.getenv("COORDINATOR_TELEGRAM_USERNAMES", ""), lower=True
            ),
            registration_mode=os.getenv("REGISTRATION_MODE", "auto").lower(),
            api_secret_key=os.getenv("API_SECRET_KEY", ""),
            admin_username=os.getenv(
                "ADMIN_USERNAME", os.getenv("ADMIN_PANEL_USERNAME", "admin")
            ),
            admin_password=os.getenv(
                "ADMIN_PASSWORD", os.getenv("ADMIN_PANEL_PASSWORD", "")
            ),
            cors_origins=_parse_list(os.getenv("CORS_ORIGINS", default_origins)),
            jwt_ttl_seconds=int(os.getenv("JWT_TTL_SECONDS", "3600")),
        )


@dataclass
class Settings:
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    web_search: WebSearchConfig = field(default_factory=WebSearchConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app=AppConfig.from_env(),
            database=DatabaseConfig.from_env(),
            ai=AIConfig.from_env(),
            web_search=WebSearchConfig.from_env(),
            telegram=TelegramConfig.from_env(),
            email=EmailConfig.from_env(),
        )


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
