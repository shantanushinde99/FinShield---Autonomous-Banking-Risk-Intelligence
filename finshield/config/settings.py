import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    duckdb_path: str = "finshield/database/finshield.duckdb"
    app_env: str = "development"
    log_level: str = "INFO"

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "finshield_memory"
    
    mistral_api_key: str = ""

    # We use pydantic_settings to automatically load from .env
    model_config = SettingsConfigDict(
        env_file=os.path.join(Path(__file__).resolve().parent.parent.parent, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
