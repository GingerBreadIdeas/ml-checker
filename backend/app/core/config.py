import os
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ML-Checker"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "dev_secret_key_change_in_production"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost/ml-checker",
    )

    # CORS
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        frontend_host = os.getenv("FRONTEND_HOST", "")
        if frontend_host:
            protocol = (
                "http" if frontend_host.startswith("localhost") else "https"
            )
            return [f"{protocol}://{frontend_host}"]
        return ["*"]

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow",
    )


settings = Settings()
