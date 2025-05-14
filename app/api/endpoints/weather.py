from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict
from app.services.weather_service import get_ultra_short_forecast, get_hourly_forecast, get_week_forecast

router = APIRouter()

@router.get("/forecast/current")
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
    
@router.get("/forecast/hourly")
async def get_hourly_weather(
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
        hour:int = 12
        weather_data = await get_hourly_forecast(lat, lon, hour)
        return weather_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.get("/week", response_model=Dict[str, Any])
async def get_weather_for_week(lat: float = 37.5665, lon: float = 126.9780):
    """
    내일부터 일주일간의 날씨 예보를 조회합니다.
    """
    try:
        return await get_week_forecast(lat, lon)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")