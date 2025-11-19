"""Application configuration settings."""

from functools import lru_cache
from typing import Any
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Priorizar variables de entorno del sistema (Railway)
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = "Football Alerts API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API para notificaciones de partidos de fútbol en vivo"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./football_alerts.db"
    
    # API-Football (Direct API, not RapidAPI)
    API_FOOTBALL_KEY: str = ""
    API_FOOTBALL_HOST: str = "v3.football.api-sports.io"
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Monitoring settings
    FAVORITE_ODDS_THRESHOLD: float = 1.35
    MONITOR_MINUTE_START: int = 55
    MONITOR_MINUTE_END: int = 62
    UPDATE_INTERVAL_SECONDS: int = 60
    
    # Ligas (IDs de API-Football)
    # Premier: 39, La Liga: 140, Serie A: 135, Bundesliga: 78, Ligue 1: 61, Colombia: 239
    LEAGUES_TO_MONITOR: str = "39,140,135,78,61,239"
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Get ALLOWED_ORIGINS as a list."""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS
    
    @property
    def leagues_to_monitor_list(self) -> list[int]:
        """Get LEAGUES_TO_MONITOR as a list of integers."""
        if isinstance(self.LEAGUES_TO_MONITOR, str):
            return [int(league_id.strip()) for league_id in self.LEAGUES_TO_MONITOR.split(",")]
        return self.LEAGUES_TO_MONITOR


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

