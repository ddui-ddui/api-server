from fastapi import APIRouter
from app.api.endpoints import walkability
from app.api.endpoints import weather
from app.api.endpoints import cache
from app.api.endpoints import commons


api_router = APIRouter()

api_router.include_router(walkability.router, prefix="/walkability", tags=["walkability"])
api_router.include_router(cache.router, prefix="/cache-check", tags=["cache check"])
api_router.include_router(commons.router, prefix="/commons", tags=["commons"])
# api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
