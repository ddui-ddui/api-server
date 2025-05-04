from fastapi import APIRouter
from app.api.endpoints import weather

api_router = APIRouter()

# 기존 라우터들...

# 날씨 API 라우터 추가
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])