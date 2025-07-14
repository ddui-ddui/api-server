from datetime import datetime
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "message": "Service is healthy"
    }