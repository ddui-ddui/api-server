from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class DogSize(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"

class Sensitivity(str, Enum):
    OBESITY = "OBESITY"               # 비만
    HIP_DYSPLASIA = "HIP_DYSPLASIA"   # 고관절 이상
    PUPPY = "PUPPY"                   # 6개월 미만
    SENIOR = "SENIOR"                 # 노견
    BRACHYCEPHALIC = "BRACHYCEPHALIC" # 단두종
    HEART_DISEASE = "HEART_DISEASE"   # 심장병
    RESPIRATORY = "RESPIRATORY"       # 호흡기 질환
    SINGLE_COAT = "SINGLE_COAT"       # 단일모
    DOUBLE_COAT = "DOUBLE_COAT"       # 이중모
    LONG_HAIR = "LONG_HAIR"           # 장모
    SHORT_HAIR = "SHORT_HAIR"         # 단모

class Location(BaseModel):
    latitude: float = Field(..., description="위도", example=37.5665)
    longitude: float = Field(..., description="경도", example=126.9780)

class Dog(BaseModel):
    size: DogSize = Field(..., description="강아지 크기")
    sensitivities: List[Sensitivity] = Field(default=[], description="강아지 민감 요소")

class WalkabilityRequest(BaseModel):
    location: Location
    region: str = Field(..., description="지역명", example="서울")
    hours: int = Field(12, description="조회할 시간 수", ge=1, le=12)
    dog: Dog