"""Central application settings loaded from environment / ``.env``."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for CuraNews.

    Values are read from environment variables and an optional ``.env`` file.
    Secrets must never be committed; use ``.env.example`` as the template.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["dev", "test", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    app_name: str = "CuraNews Aggregator"

    database_url: str = Field(
        default="postgresql+psycopg://curanews:curanews@localhost:5432/curanews",
        description="SQLAlchemy database URL (PostgreSQL — Phase 3).",
    )
    sqlite_path: str = Field(
        default="data/local/curanews.sqlite3",
        description="SQLite path used by Scrapy pipelines (Issue #5).",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for cache and scrape locks.",
    )

    spacy_model: str = "en_core_web_sm"
    feed_cache_ttl_seconds: int = Field(default=120, ge=1)
    scrape_max_retries: int = Field(default=5, ge=0)
    scrape_backoff_base: float = Field(default=0.5, gt=0)
    scrape_concurrency: int = Field(default=2, ge=1)

    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)

    pii_hash_salt: str = Field(
        default="change-me-in-local-only",
        description="Salt for PII pseudonymization (override in real .env).",
    )

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
