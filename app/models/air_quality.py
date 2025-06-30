from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class HourlyForecast(BaseModel):
    base_date: str
    base_time: str  
    pm10_grade: int
    pm25_grade: int

class WeeklyForecast(BaseModel):
    base_date: str
    air_quality_score: int

class HourlyAirQualityCache(BaseModel):
    """시간별 대기질 캐시 모델 (12시간)"""
    forecasts: Dict[str, Any]
    cached_at: str

class WeeklyAirQualityCache(BaseModel):
    """주간별 대기질 캐시 모델 (5일)"""
    forecasts: List[Dict[str, Any]]
    cached_at: str
