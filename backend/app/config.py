from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field, field_validator
from functools import lru_cache
from pathlib import Path
import secrets

# Get the project root (osfeed/)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):

    # OpenRouter API (optional - used for free LLM fallback)
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"

    # OpenAI API (Translations & Embeddings)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Application
    preferred_language: str = "en"
    summary_time: str = "08:00"
    app_debug: bool = False

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "osfeed_db"
    postgres_user: str = "osfeed_user"
    postgres_password: str = ""

    # Legacy SQLite (for fallback/migration)
    use_sqlite: bool = False  # Set to True for local dev without PostgreSQL
    sqlite_url: str = "sqlite+aiosqlite:///./data/osfeed.db"

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

    # Security Headers
    security_headers_enabled: bool = True  # Enable security headers middleware
    security_csp_enabled: bool = True  # Enable Content-Security-Policy header
    security_csp_directives: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    security_hsts_enabled: bool = True  # Enable Strict-Transport-Security header
    security_hsts_max_age: int = 31536000  # HSTS max-age in seconds (1 year)
    security_hsts_include_subdomains: bool = True  # Include subdomains in HSTS
    security_x_frame_options: str = "DENY"  # X-Frame-Options value (DENY, SAMEORIGIN)
    security_x_content_type_options: bool = True  # Enable X-Content-Type-Options: nosniff
    security_referrer_policy: str = "strict-origin-when-cross-origin"  # Referrer-Policy value
    security_permissions_policy: str = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )

    # Email Configuration
    email_enabled: bool = False  # Default to False so app works without email
    email_provider: str = "smtp"  # "smtp", "resend"
    email_from_address: str = "noreply@osfeed.app"
    email_from_name: str = "OSFeed"

    # SMTP Settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    # Resend Settings (alternative)
    resend_api_key: str = ""

    # Token Settings
    password_reset_token_expire_minutes: int = 30
    email_verification_token_expire_hours: int = 24

    # Redis Cache
    redis_url: str = ""
    redis_cache_ttl_seconds: int = 86400
    enable_response_cache: bool = True
    response_cache_ttl: int = 30

    # Translation concurrency
    translation_concurrency: int = 20  # Increased from 10 for better throughput

    # Translation cost optimization
    translation_default_model: str = "gemini-flash"  # Options: gemini-flash, gpt-4o-mini, google
    translation_high_priority_model: str = "gpt-4o-mini"  # Model for high-priority messages
    translation_skip_same_language: bool = True  # Skip if source == target
    translation_skip_trivial: bool = True  # Skip URLs-only, emojis-only, etc.
    translation_skip_short_words: list[str] = [
        "ok",
        "okay",
        "yes",
        "no",
        "yep",
        "nope",
        "oui",
        "non",
        "si",
        "ja",
        "nein",
        "\u0434\u0430",
        "\u043d\u0435\u0442",
    ]
    translation_skip_short_max_chars: int = 2
    translation_high_priority_hours: int = 24  # Messages < 24h = high priority
    translation_normal_priority_days: int = 7  # Messages 1-7 days = normal priority
    translation_high_quality_languages: list[str] = ["ru", "uk", "fr", "de", "es", "it"]

    # Gemini API (for cost-effective translation)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Adaptive cache TTL
    translation_cache_base_ttl: int = 604800  # 7 days base TTL
    translation_cache_max_ttl: int = 2592000  # 30 days max TTL
    translation_cache_hit_multiplier: float = 1.5  # TTL multiplier per hit

    # Translation memory cache
    translation_memory_cache_max_size: int = 1000  # Max number of entries in LRU cache

    # Fetch parallelization
    fetch_workers: int = 10  # Number of parallel fetch workers

    # Database pooling (PostgreSQL)
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800

    # Audit Logs
    audit_log_retention_days: int = 365
    audit_log_purge_time: str = "02:30"

    # API Usage Tracking
    api_usage_tracking_enabled: bool = True
    llm_cost_input_per_1k: float = 0.0
    llm_cost_output_per_1k: float = 0.0

    # Telegram API (User Account)
    telegram_api_id: int = 0

    @field_validator("telegram_api_id", mode="before")
    @classmethod
    def parse_telegram_api_id(cls, v):
        if v == "" or v is None:
            return 0
        return v
    telegram_api_hash: str = ""
    telegram_phone: str = ""
    telegram_session_path: str = "/app/data/telegram.session"
    telegram_session_string: str = ""  # StringSession for cloud deployments (takes priority over file)

    # Telegram Rate Limits (Redis Token Bucket)
    telegram_requests_per_minute: int = 30
    telegram_flood_wait_multiplier: float = 1.5
    telegram_max_retries: int = 3

    # JoinChannel Limit (Telegram enforces ~20/day)
    telegram_join_channel_daily_limit: int = 20
    telegram_join_channel_queue_enabled: bool = True

    # Telegram Worker Config
    telegram_fetch_workers: int = 3
    telegram_batch_size: int = 100
    telegram_sync_interval_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Singleton instance for easy import
settings = get_settings()
