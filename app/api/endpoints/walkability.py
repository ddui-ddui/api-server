from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict
from app.services.walkability_service import get_walkability_current as service_get_current, get_walkability_hourly as service_get_hourly, get_walkability_weekly as service_get_weekly, get_walkability_current_detail as service_get_current_detail
from app.models.response import success_response, error_response

router = APIRouter()

@router.get("/current")
async def get_walkability_current (
    lat: float = Query(37.6419399, description="위도"),
    lon: float = Query(127.0170059, description="경도"),
    dog_size: str = Query("medium", description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)"),
    air_quality_type: str = Query("korean", description="대기질 기준 (korean/who)"),
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param dog_size: 견종 크기 (small/medium/large)
    :param sensitivities: 민감군 목록 (쉼표로 구분)
    :param air_quality_type: 대기질 기준 (korean/who)
    :return: 현재 날씨 정보
    """
    try:
        walkability = await service_get_current(lat, lon, dog_size, sensitivities, air_quality_type)
        return success_response(data=walkability)
    except Exception as e:
        raise error_response(500, f"서버 오류: {str(e)}")

@router.get("/hourly")
async def get_walkability_hourly (
    lat: float = Query(37.6419378, description="위도"),
    lon: float = Query(127.0170019, description="경도"),
    hours: int = Query(12, description="시간 (0-12)", ge=1, le=12),
    dog_size: str = Query("medium", description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)"),
    air_quality_type: str = Query("korean", description="대기질 기준 (korean/who)"),
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
        walkability = await service_get_hourly(lat, lon, hours, dog_size, sensitivities, air_quality_type)
        return success_response(data=walkability)
    except Exception as e:
        raise error_response(500, f"서버 오류: {str(e)}")

@router.get("/weekly")
async def get_walkability_weekly (
    lat: float = Query(37.5665, description="위도"),
    lon: float = Query(126.9780, description="경도"),
    region: str = Query("서울", description="지역명"),
    days: int = Query(7, description="일자 (1~7)", ge=1, le=7),
    dog_size: str = Query("medium", description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)"),
    air_quality_type: str = Query("korean", description="대기질 기준 (korean/who)"),
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param region: 지역명
    :param days: 일자 (1~7)
    :return: 현재 날씨 정보
    """
    try:
        walkability = await service_get_weekly(lat, lon, region, days, dog_size, sensitivities, air_quality_type)
        return success_response(data=walkability)
    except Exception as e:
        raise error_response(500, f"서버 오류: {str(e)}")
    
@router.get("/current/detail")
async def get_walkability_current_detail (
    lat: float = Query(37.6419399, description="위도"),
    lon: float = Query(127.0170059, description="경도")
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :return: 현재 날씨 상세 정보
    """
    try:
        walkability = await service_get_current_detail(lat, lon)
        return success_response(data=walkability)
    except Exception as e:
        raise error_response(500, f"서버 오류: {str(e)}")