"""Configuration management via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PRODUCTION_LLM_MODEL: str = "llama3"
    CANARY_LLM_MODEL: str = "llama3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 60
    RISK_THRESHOLD_LOW: float = 0.4
    RISK_THRESHOLD_HIGH: float = 0.7
    RATE_LIMIT_PER_MINUTE: int = 30
    CANARY_TOKEN_PREFIX: str = "syren-canary"
    CANARY_DOMAIN: str = "siren.corp"
    CANARY_DB_PASSWORD: str = "Syren$DeCoY"
    LOG_LEVEL: str = "INFO"
    AUDIT_LOG_FILE: str = "logs/audit.jsonl"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_WORKERS: int = 1


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton pattern)."""
    return Settings()