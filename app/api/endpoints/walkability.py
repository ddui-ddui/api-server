from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict
from app.services.walkability_service import get_walkability_houly

from app.models.walkability import WalkabilityRequest

router = APIRouter()

@router.get("/walkability/hourly")
async def get_walkability_hourly (
    lat: float = Query(37.5665, description="위도"),
    lon: float = Query(126.9780, description="경도"),
    region: str = Query("서울", description="지역명"),
    hours: int = Query(12, description="시간 (0-12)", ge=1, le=12),
    dog_size: str = Query("medium", description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)")
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param region: 지역명
    :param hour: 시간 (0-12)
    :return: 현재 날씨 정보
    """
    try:
        walkability = await get_walkability_houly(lat, lon, region, hours, dog_size, sensitivities)
        return walkability
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")