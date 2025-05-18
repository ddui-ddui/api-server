from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_URL: str = "/api/v1"
    PROJECT_NAME: str = "DDUI DDUI API Server"
    
    DEBUG: bool = False
    SSL_VERIFY: bool = True

    # Server Info
    HOST: str = "127.0.0.1"
    PORT: int = 3500

    # GOV API INFO
    GOV_DATA_API_KEY: str = ""
    GOV_DATA_BASE_URL: str = "https://apis.data.go.kr"
    
    # Weather API URL
    GOV_DATA_WEATHER_ULTRA_SHORT_URL: str = ""
    GOV_DATA_WEATHER_SHORT_URL: str = ""
    GOV_DATA_WEATHER_MID_OUTLOOK_URL: str = ""
    GOV_DATA_WEATHER_MID_LAND_URL: str = ""
    
    # Air Quality API URL
    GOV_DATA_AIRQUALITY_NEARSATIONS_URL: str = ""
    GOV_DATA_AIRQUALITY_STATION_URL: str = ""
    GOV_DATA_AIRQUALITY_HOURLY_URL: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings()