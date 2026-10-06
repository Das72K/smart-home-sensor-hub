"""
Application configuration module.

Loads settings from environment variables (.env file).
Uses Pydantic for validation and type safety.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Database
    database_url: str = "postgresql://hub_user:hub_secure_pass_123@localhost:5432/smart_home_hub"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Single instance used throughout the app
settings = Settings()
