from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict
from app.services.weather_service import get_ultra_short_forecast

router = APIRouter()

@router.get("/current")
async def get_current_weather(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도")
) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :return: 현재 날씨 정보
    """
    try:
        weather_data = await get_ultra_short_forecast(lat, lon)
        return weather_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")