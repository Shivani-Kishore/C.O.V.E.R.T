"""
Configuration Settings for C.O.V.E.R.T Backend
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings"""

    # ===== Application =====
    APP_NAME: str = "C.O.V.E.R.T"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ===== Security =====
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ===== CORS =====
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ===== Database =====
    DATABASE_URL: str = "postgresql+asyncpg://covert_user:covert_password@localhost:5432/covert_db"
    DB_ECHO: bool = False

    # ===== Redis =====
    REDIS_URL: str = "redis://localhost:6379/0"

    # ===== IPFS =====
    IPFS_API_URL: str = "/ip4/127.0.0.1/tcp/5001"
    IPFS_GATEWAY_URL: str = "http://localhost:8080"
    PINATA_API_KEY: str = ""
    PINATA_SECRET_KEY: str = ""
    WEB3_STORAGE_TOKEN: str = ""

    # ===== Blockchain =====
    RPC_URL: str = "http://localhost:8545"
    CHAIN_ID: int = 31337  # Local Anvil
    COMMITMENT_REGISTRY_ADDRESS: str = ""
    DAILY_ANCHOR_ADDRESS: str = ""
    REPUTATION_SBT_ADDRESS: str = ""

    # ===== Rate Limiting =====
    RATE_LIMIT_SUBMISSIONS: int = 10  # per hour
    RATE_LIMIT_GENERAL: int = 100  # per hour

    # ===== File Upload =====
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".mp4", ".zip"]

    # ===== Monitoring =====
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
