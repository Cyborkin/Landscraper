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


settings = Settings()
