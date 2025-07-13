from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
import os

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # API
    API_V1_URL: str = "/api/v1"
    PROJECT_NAME: str = "DDUI DDUI API Server"

    # Server Info
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=3500, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")
    TIMEOUT: int = Field(default=30, env="TIMEOUT")
    RELOAD: bool = Field(default=False, env="RELOAD")
    
    # Logging
    LOG_LEVEL: str = Field(default="debug", env="LOG_LEVEL")

    # SSL
    SSL_VERIFY: bool = Field(default=False, env="SSL_VERIFY")

    # GOV API INFO
    GOV_DATA_API_KEY_1: str = ""
    GOV_DATA_API_KEY_2: str = ""
    GOV_DATA_BASE_URL: str = "https://apis.data.go.kr"
    
    # Weather API URL
    GOV_DATA_WEATHER_ULTRA_SHORT_URL: str = ""
    GOV_DATA_WEATHER_SHORT_URL: str = ""
    GOV_DATA_WEATHER_MID_OUTLOOK_URL: str = ""
    GOV_DATA_WEATHER_MID_LAND_URL: str = ""
    GOV_DATA_WEATHER_SEARCH_AREA_URL: str = ""
    GOV_DATA_WEATHER_SEARCH_PREV_URL: str = ""
    GOV_DATA_WEATHER_LIVING_UV_URL: str = ""

    # Astronomy API URL
    GOV_DATA_ASTRONOMY_SUN_URL: str = ""
    
    # Air Quality API URL
    GOV_DATA_AIRQUALITY_NEARSATIONS_URL: str = ""
    GOV_DATA_AIRQUALITY_STATION_URL: str = ""
    GOV_DATA_AIRQUALITY_HOURLY_URL: str = ""
    GOV_DATA_AIRQUALITY_WEEKLY_URL: str = ""

    # Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

settings = Settings()