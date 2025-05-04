import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_URL: str = "/api/v1"
    PROJECT_NAME: str = "DDUI DDUI API Server"
    
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # SSL 검증
    SSL_VERIFY: bool = os.getenv("SSL_VERIFY", "True").lower() == "true"

    
    # Weather API
    GOV_DATA_API_KEY: str = os.getenv("GOV_DATA_API_KEY", "")
    GOV_DATA_BASE_URL: str = os.getenv("GOV_DATA_BASE_URL", "https://apis.data.go.kr")
    GOV_DATA_WEATHER_ULTRA_SHORT_URL: str = os.getenv("GOV_DATA_WEATHER_ULTRA_SHORT_URL", "")
    GOV_DATA_WEATHER_SHORT_URL: str = os.getenv("GOV_DATA_WEATHER_SHORT_URL", "")
    
    # Server Info
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 3500))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()