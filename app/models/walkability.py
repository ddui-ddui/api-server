from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class DogSize(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"

class Location(BaseModel):
    latitude: float = Field(..., description="위도", example=37.5665)
    longitude: float = Field(..., description="경도", example=126.9780)

class Dog(BaseModel):
    size: DogSize = Field(..., description="강아지 크기")
    # sensitivities: List[Sensitivity] = Field(default=[], description="강아지 민감 요소")

class WalkabilityRequest(BaseModel):
    location: Location
    dog: Dog

class WalkabilityLevel(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    MODERATE = "MODERATE"
    POOR = "POOR"
    BAD = "BAD"

class WalkabilityScore(BaseModel):
    score: int = Field(..., description="산책 적합도 점수 (0-100)", example=85)
    level: WalkabilityLevel = Field(..., description="산책 적합도 등급")

class WeatherInfo(BaseModel):
    temperature: float = Field(..., description="기온 (℃)")
    humidity: int = Field(..., description="습도 (%)")
    precipitation_type: int = Field(..., description="강수형태 (0:없음, 1:비, 2:비/눈, 3:눈, 4:소나기)")
    rainfall: float = Field(..., description="1시간 강수량 (mm)")
    sky_condition: int = Field(..., description="하늘상태 (1:맑음, 3:구름많음, 4:흐림)")
    wind_speed: float = Field(..., description="풍속 (m/s)")
    dust_level: str = Field(..., description="미세먼지 등급")
    forecast_time: str = Field(..., description="예보 시간")

class WalkabilityResponse(BaseModel):
    walkability: WalkabilityScore
    weather: WeatherInfo