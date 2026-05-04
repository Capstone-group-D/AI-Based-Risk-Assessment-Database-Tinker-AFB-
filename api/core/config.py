from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "PPE Recommendation Engine API"
    VERSION: str = "0.1.0"
    
    # Database Settings
    DATABASE_URL: str = ""  # Keeping it empty for now until DB is fully connected

    # API Key — set in .env to enable key-based auth; empty string disables auth (dev mode)
    API_KEY: str = ""

    # JWT — set to a long random string to enable JWT user auth; empty disables JWT
    JWT_SECRET_KEY: str = ""

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Admin Settings
    ADMIN_MASTER_PASSWORD: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
