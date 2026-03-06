import os

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "LANDSCRAPER_"}

    # Database
    database_url: str = "postgresql+asyncpg://landscraper:landscraper@localhost:5432/landscraper"

    # Redis
    redis_url: str = "redis://redis:6379/1"  # db 1 to avoid iranwatch collision

    # LLM
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_cloud_model: str = "claude-sonnet-4-20250514"
    default_local_model: str = "qwen2.5:7b"

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "LandScraper"
    langsmith_tracing_enabled: bool = True

    # Scraping
    scrape_rate_limit_seconds: float = 2.0
    playwright_headless: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @model_validator(mode="before")
    @classmethod
    def _bridge_railway_env_vars(cls, values: dict) -> dict:
        """Accept Railway's standard env vars as fallbacks.

        Railway addons set DATABASE_URL, REDIS_URL, and PORT directly.
        Map them to our LANDSCRAPER_-prefixed names when the prefixed
        versions aren't explicitly set.
        """
        # DATABASE_URL — also convert postgres:// and postgresql:// to asyncpg
        if not values.get("database_url") and not os.environ.get("LANDSCRAPER_DATABASE_URL"):
            raw = os.environ.get("DATABASE_URL", "")
            if raw:
                url = raw.replace("postgres://", "postgresql+asyncpg://", 1)
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
                values["database_url"] = url

        # REDIS_URL
        if not values.get("redis_url") and not os.environ.get("LANDSCRAPER_REDIS_URL"):
            raw = os.environ.get("REDIS_URL", "")
            if raw:
                values["redis_url"] = raw

        # PORT
        if not values.get("api_port") and not os.environ.get("LANDSCRAPER_API_PORT"):
            port = os.environ.get("PORT", "")
            if port:
                values["api_port"] = int(port)

        return values


settings = Settings()
