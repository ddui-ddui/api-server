from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict
from app.services.walkability_service import get_walkability_current as service_get_current, get_walkability_hourly as service_get_hourly, get_walkability_weekly as service_get_weekly, get_walkability_current_detail as service_get_current_detail
from app.models.response import success_response, error_response
from app.models.walkability import DogSize, CoatType, CoatLength, AirQualityType
from app.validate.request_sensitive import validate_sensitivities
from app.config.logging_config import get_logger

router = APIRouter()
logger = get_logger()

@router.get("/current")
async def get_walkability_current (
    lat: float = Query(37.499, description="위도"),
    lon: float = Query(127.103, description="경도"),
    dog_size: DogSize = Query(DogSize.small, description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)"),
    coat_type: CoatType = Query(CoatType.double, description="모피 종류 (single/double)"),
    coat_length: CoatLength = Query(CoatLength.long, description="모피 길이 (short/long)"),
    air_quality_type: AirQualityType = Query(AirQualityType.who, description="대기질 기준 (korean/who)"),
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
        # 민감군 목록 검증
        validate_sensitivities(sensitivities)
        air_quality_type = f"{air_quality_type.value}_standard"
        logger.info(f"실시간 API: {lat}, lon: {lon}, dog_size: {dog_size.value}, sensitivities: {None if sensitivities == '' else sensitivities}, coat_type: {coat_type.value}, coat_length: {coat_length.value}, air_quality_type: {air_quality_type}")
        walkability = await service_get_current(lat, lon, dog_size.value, sensitivities, coat_type.value, coat_length.value, air_quality_type)
        return success_response(data=walkability)
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(500, f"실시간 날씨 조회 오류: {str(e)}")

@router.get("/hourly")
async def get_walkability_hourly (
lat: float = Query(37.641, description="위도"),
    lon: float = Query(127.017, description="경도"),
    hours: int = Query(12, description="시간 (0-12)", ge=1, le=12),
    dog_size: DogSize = Query(DogSize.small, description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)"),
    coat_type: CoatType = Query(CoatType.double, description="모피 종류 (single/double)"),
    coat_length: CoatLength = Query(CoatLength.long, description="모피 길이 (short/long)"),
    air_quality_type: AirQualityType = Query(AirQualityType.who, description="대기질 기준 (korean/who)"),
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param hour: 시간 (0-12)
    :param dog_size: 견종 크기 (small/medium/large)
    :param sensitivities: 민감군 목록 (쉼표로 구분)
    :param air_quality_type: 대기질 기준 (korean/who)
    :return: 현재 날씨 정보
    """
    try:
        # 민감군 목록 검증
        validate_sensitivities(sensitivities)
        air_quality_type = f"{air_quality_type.value}_standard"
        logger.info(f"시간별 API: {lat}, lon: {lon}, hours: {hours}, dog_size: {dog_size.value}, sensitivities: {None if sensitivities == '' else sensitivities}, coat_type: {coat_type.value}, coat_length: {coat_length.value}, air_quality_type: {air_quality_type}")
        walkability = await service_get_hourly(lat, lon, hours, dog_size.value, sensitivities, coat_type.value, coat_length.value, air_quality_type)
        return success_response(data=walkability)
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(500, f"시간별 날씨 조회 오류: {str(e)}")

@router.get("/weekly")
async def get_walkability_weekly (
    lat: float = Query(37.566, description="위도"),
    lon: float = Query(126.978, description="경도"),
    days: int = Query(7, description="일자 (1~7)", ge=1, le=7),
    dog_size: DogSize = Query(DogSize.small, description="견종 크기 (small/medium/large)"),
    sensitivities: str = Query("", description="민감군 목록 (쉼표로 구분)"),
    coat_type: CoatType = Query(CoatType.double, description="모피 종류 (single/double)"),
    coat_length: CoatLength = Query(CoatLength.long, description="모피 길이 (short/long)"),
    air_quality_type: AirQualityType = Query(AirQualityType.who, description="대기질 기준 (korean/who)"),
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param days: 일자 (1~7)
    :param dog_size: 견종 크기 (small/medium/large)
    :param sensitivities: 민감군 목록 (쉼표로 구분)
    :param air_quality_type: 대기질 기준 (korean/who)
    :return: 현재 날씨 정보
    """
    try:
        # 민감군 목록 검증
        validate_sensitivities(sensitivities)
        air_quality_type = f"{air_quality_type.value}_standard"
        logger.info(f"주간별 API: {lat}, lon: {lon}, days: {days}, dog_size: {dog_size.value}, sensitivities: {None if sensitivities == '' else sensitivities}, coat_type: {coat_type.value}, coat_length: {coat_length.value}, air_quality_type: {air_quality_type}")
        walkability = await service_get_weekly(lat, lon, days, dog_size.value, sensitivities, coat_type.value, coat_length.value, air_quality_type)
        return success_response(data=walkability)
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(500, f"주간별 날씨 조회 오류: {str(e)}")
    
@router.get("/current/detail")
async def get_walkability_current_detail (
    lat: float = Query(37.641, description="위도"),
    lon: float = Query(127.017, description="경도")
    ) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :return: 현재 날씨 상세 정보
    """
    try:
        logger.info(f"실시간 상세 API: {lat}, lon: {lon}")
        walkability = await service_get_current_detail(lat, lon)
        return success_response(data=walkability)
    except HTTPException:
        raise
    except Exception as e:
        raise error_response(500, f"실시간 상세 날씨 조회 오류: {str(e)}")