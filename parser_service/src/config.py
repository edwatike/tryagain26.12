"""Configuration for Parser Service."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parser Service settings."""
    
    CHROME_CDP_URL: str = "http://127.0.0.1:9222"
    LOG_LEVEL: str = "INFO"
    
    # Timeouts
    page_load_timeout: int = 30000  # 30 seconds
    navigation_timeout: int = 60000  # 60 seconds
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    @property
    def chrome_cdp_url(self) -> str:
        """Backward compatibility."""
        return self.CHROME_CDP_URL
    
    @property
    def log_level(self) -> str:
        """Backward compatibility."""
        return self.LOG_LEVEL


settings = Settings()

