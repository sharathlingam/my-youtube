from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "AI YouTube API"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/yt_pwa"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Redis (Upstash)
    redis_url: str = "redis://localhost:6379"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # YouTube Data API
    youtube_api_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5050", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
