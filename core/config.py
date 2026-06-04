from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI-Wealth-System"
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "change-me"
    debug: bool = True
    log_level: str = "INFO"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # AI APIs
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    primary_llm_provider: Literal["openai", "anthropic", "local"] = "anthropic"

    local_llm_enabled: bool = False
    local_llm_base_url: str = "http://localhost:11434"
    local_llm_model: str = "llama3"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_wealth"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_celery_broker: str = "redis://localhost:6379/1"
    redis_celery_backend: str = "redis://localhost:6379/2"

    # Vector Store
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection_prefix: str = "ai_wealth"

    # Search
    serper_api_key: str = ""
    google_search_api_key: str = ""
    google_search_engine_id: str = ""
    default_search_provider: Literal["duckduckgo", "serper", "google"] = "duckduckgo"

    # System Behaviour
    research_loop_interval_minutes: int = 30
    ceo_review_interval_minutes: int = 60
    max_concurrent_agents: int = 10
    opportunity_score_threshold: int = 65
    max_execution_budget_usd: float = 50.0

    # Memory
    short_term_ttl_seconds: int = 3600
    long_term_retention_days: int = 365
    max_vector_results: int = 10

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def active_llm_model(self) -> str:
        if self.primary_llm_provider == "openai":
            return self.openai_model
        elif self.primary_llm_provider == "anthropic":
            return self.anthropic_model
        return self.local_llm_model


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
