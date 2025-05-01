import os
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DDUI DDUI API Server"
    
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Weather API
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_URL: str = os.getenv("WEATHER_API_URL", "http://api.weatherapi.com/v1")
    
    # Server Info
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 3500))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()