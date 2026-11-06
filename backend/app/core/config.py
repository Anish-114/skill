from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "SkillBridge AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration (defaults to SQLite; can be overridden via DATABASE_URL env var)
    DATABASE_URL: str = "sqlite:///./skillbridge.db"
    
    # JWT & Auth configuration
    SECRET_KEY: str = "skillbridge-ai-super-secret-development-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Events Synchronization Configuration
    EVENTS_SYNC_TOKEN: str = "skillbridge-events-sync-secret-token"
    EVENTS_SYNC_INTERVAL_HOURS: int = 6
    EVENTS_SYNC_SOURCES: str = "devfolio,unstop,mlh,sih"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
