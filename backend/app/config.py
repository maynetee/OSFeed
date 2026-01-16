from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from functools import lru_cache
from pathlib import Path
import secrets

# Get the project root (telescope/)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # Telegram API
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str

    # OpenRouter API
    openrouter_api_key: str
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"

    # OpenAI API (Translations)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Application
    preferred_language: str = "en"
    summary_time: str = "08:00"
    app_debug: bool = False

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "telescope_db"
    postgres_user: str = "telescope_user"
    postgres_password: str = ""

    # Legacy SQLite (for fallback/migration)
    use_sqlite: bool = False  # Set to True for local dev without PostgreSQL
    sqlite_url: str = "sqlite+aiosqlite:///./data/telescope.db"

    @computed_field
    @property
    def database_url(self) -> str:
        """Return the appropriate database URL based on configuration."""
        if self.use_sqlite:
            return self.sqlite_url
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Authentication - JWT
    secret_key: str = secrets.token_urlsafe(32)  # Generate random if not set
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1 hour
    refresh_token_expire_days: int = 7
    scheduler_enabled: bool = True

    # Telegram Rate Limiting / Flood Wait Management
    telegram_max_retries: int = 5
    telegram_base_delay: float = 1.0  # seconds
    telegram_max_delay: float = 300.0  # 5 minutes max
    telegram_jitter: bool = True
    telegram_concurrent_channels: int = 3  # max parallel channel fetches

    # Pinecone Vector Store
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "telescope-embeddings"
    pinecone_namespace: str = "messages"
    pinecone_metric: str = "cosine"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Deduplication
    dedup_similarity_threshold: float = 0.85
    dedup_top_k: int = 5

    # Audit Logs
    audit_log_retention_days: int = 365
    audit_log_purge_time: str = "02:30"

    # API Usage Tracking
    api_usage_tracking_enabled: bool = True
    llm_cost_input_per_1k: float = 0.0
    llm_cost_output_per_1k: float = 0.0

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Singleton instance for easy import
settings = get_settings()
