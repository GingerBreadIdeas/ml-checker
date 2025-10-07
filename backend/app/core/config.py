import os
from typing import Optional, Dict, Any, List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "ML-Checker"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost/ml-checker"
    )

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # For development

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
