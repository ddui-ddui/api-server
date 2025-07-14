from multiprocessing.util import get_logger
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.response import error_response, success_response
from app.services.cache_service import AirQualityCacheService
router = APIRouter()
logger = get_logger()

@router.get("/air_quality/hourly")
async def get_air_quality_hourly () -> Dict[str, Any]:
    """
    시간별 대기질 캐시 확인용
    """
    try:
        cached_data = await AirQualityCacheService().get_hourly_cache()
        if cached_data:
            return success_response(data=cached_data)
        else:
            raise error_response(404, "시간별 대기질 캐시가 존재하지 않습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(500, f"시간별 캐시 조회 오류: {str(e)}")

@router.get("/air_quality/weekly")
async def get_air_quality_weekly () -> Dict[str, Any]:
    """
    일별 대기질 캐시 확인용
    """
    try:
        cached_data = await AirQualityCacheService().get_weekly_cache()
        if cached_data:
            return success_response(data=cached_data)
        else:
            raise error_response(404, "주간별 대기질 캐시가 존재하지 않습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(500, f"주간별 캐시 조회 오류: {str(e)}")