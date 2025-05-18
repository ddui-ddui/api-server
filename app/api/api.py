from fastapi import APIRouter
from app.api.endpoints import walkability


api_router = APIRouter()

api_router.include_router(walkability.router, prefix="/walkability", tags=["walkability"])
