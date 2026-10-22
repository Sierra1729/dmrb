"""Application configuration settings."""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "dmrv"
    PRODUCT_NAME: str = "CarbonBridge dMRV"
    FIRM_NAME: str = "GreenConsult India"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretjwtkeyforlocaldevelopment_changeinproduction32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = "sqlite:///./dmrv.db"  # default local SQLite, override with Postgres in docker
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "miniopassword"
    MINIO_BUCKET_NAME: str = "dmrv-evidence-vault"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
