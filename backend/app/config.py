"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration – every field has a dev-safe default."""

    # ── General ──────────────────────────────────────────────────────────
    ENV: str = "dev"
    DATABASE_URL: str = "postgresql+asyncpg://muhurta:muhurta@db:5432/muhurta"
    JWT_SECRET: str = "REPLACE_ME"
    FERNET_KEY: str = "REPLACE_ME"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    INTERNAL_API_KEY: str = "REPLACE_ME"
    ADMIN_EMAILS: str = ""

    # ── LLM providers ───────────────────────────────────────────────────
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = "REPLACE_ME"
    OPENAI_MODEL: str = "REPLACE_ME"
    ANTHROPIC_API_KEY: str = "REPLACE_ME"
    ANTHROPIC_MODEL: str = "REPLACE_ME"
    GROQ_API_KEY: str = "REPLACE_ME"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Google OAuth ─────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = "REPLACE_ME"
    GOOGLE_CLIENT_SECRET: str = "REPLACE_ME"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Telegram ─────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = "REPLACE_ME"
    TELEGRAM_BOT_USERNAME: str = "REPLACE_ME"
    TELEGRAM_WEBHOOK_SECRET: str = "REPLACE_ME"

    @property
    def admin_email_list(self) -> list[str]:
        """Parse comma-separated admin emails into a list."""
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def get_settings() -> Settings:
    """Factory consumed by FastAPI ``Depends``."""
    return Settings()
