"""
Application configuration using Pydantic Settings.
Reads settings from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:CHANGE_ME@localhost:5432/b2bplatform"

    # Parser Service
    PARSER_SERVICE_URL: str = "http://127.0.0.1:9003"

    # Ollama INN Extractor Service
    OLLAMA_SERVICE_URL: str = "http://127.0.0.1:9004"

    # Checko API
    CHECKO_API_KEY: str = ""

    # Application
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_SQL: bool = False

    # CORS - парсим из строки, разделенной запятыми
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Storage
    ATTACHMENTS_DIR: str = "storage/attachments"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Create a singleton instance
settings = Settings()

# Backward compatibility: add properties for lowercase access
Settings.database_url = property(lambda self: self.DATABASE_URL)
Settings.parser_service_url = property(lambda self: self.PARSER_SERVICE_URL)
Settings.env = property(lambda self: self.ENV)
Settings.log_level = property(lambda self: self.LOG_LEVEL)
Settings.log_sql = property(lambda self: self.LOG_SQL)
Settings.attachments_dir = property(lambda self: self.ATTACHMENTS_DIR)
Settings.cors_origins = property(lambda self: self.CORS_ORIGINS)
Settings.checko_api_key = property(lambda self: self.CHECKO_API_KEY)
Settings.ollama_service_url = property(lambda self: self.OLLAMA_SERVICE_URL)
