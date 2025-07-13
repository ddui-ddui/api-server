from datetime import datetime
from fastapi import APIRouter
from app.api.endpoints import walkability
from app.api.endpoints import weather


api_router = APIRouter()

@api_router.get("/health")
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "message": "Service is healthy"
    }

api_router.include_router(walkability.router, prefix="/walkability", tags=["walkability"])
# api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
