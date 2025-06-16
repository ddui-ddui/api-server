from typing import Any, Dict

from fastapi import HTTPException
from app.services.weather_service import get_ultra_short_forecast, get_hourly_forecast, get_weekly_forecast, get_weather_uvindex
from app.services.astronomy_service import get_sunrise_sunset
from app.services.air_quality import get_current_air_quality, get_hourly_air_quality, get_weekly_air_quality
from app.utils.walkability_calculator import WalkabilityCalculator
from app.utils.airquality_calculator import calculate_air_quality_score_avg
from app.utils.temperature_calculator import calculate_apparent_temperature
from app.config.logging_config import get_logger
logger = get_logger()

# 산책 적합도 계산기
walkability_calculator = WalkabilityCalculator()
async def get_walkability_current(
    lat: float, 
    lon: float, 
    dog_size: str = "medium", 
    sensitive_groups: list = None,
    air_quality_type: str = "korean") -> Dict[str, Any]:
    
    results = {}
    # 현재 날씨 조회
    fields = ["temperature", "precipitation_type", "sky_condition", "min_temperature", "max_temperature", "previous_temperature", "temperature_difference", "uv_index", "lightning"]
    weather_data = await get_ultra_short_forecast(lat, lon, fields)
    if not weather_data:
        logger.error(f"날씨 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    results["weather"] = weather_data
    
    # 현재 대기질 정보 조회
    air_quality_data = await get_current_air_quality(lat, lon, air_quality_type)
    if not air_quality_data:
        logger.error(f"대기질 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="대기질 정보를 찾을 수 없습니다.")
    
    results["air_quality"] = air_quality_data

    # 산책 적합도 점수 계산
    try:
        walkability_data = walkability_calculator.calculate_walkability_score(
            temperature=weather_data["temperature"],
            pm10_grade=air_quality_data["pm10_grade"],
            pm10_value=air_quality_data["pm10_value"],
            pm25_grade=air_quality_data["pm25_grade"],
            pm25_value=air_quality_data["pm25_value"],
            precipitation_type=weather_data["precipitation_type"],
            sky_condition=weather_data["sky_condition"],
            dog_size=dog_size,
            air_quality_type=air_quality_type
        )
        results["walkability"] = {
            "score": walkability_data.get("walkability_score"),
            "grade": walkability_data.get("walkability_grade")
        }
    except Exception as e:
        logger.error(f"산책 적합도 점수 계산 실패: {str(e)}")
        results["walkability_score"] = {
            "score": 50  # 중간 값으로 기본 설정
        }
    
    return {"forecasts": results}

async def get_walkability_hourly(
    lat: float, 
    lon: float, 
    hours: int = 12, 
    dog_size: str = "medium", 
    sensitive_groups: list = None,
    air_quality_type: str = "korean") -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param hour: 시간 (0-12)
    :param dog_size: 견종 크기 (small/medium/large)
    :param air_quality_type: 대기질 기준 (korean/who)
    :return: 현재 날씨 정보
    """

    if(hours > 12):
        logger.error(f"시간 조회 오류: {hours}시간은 최대 12시간까지만 가능합니다.")
        raise HTTPException(status_code=400, detail="최대 12시간까지만 조회 가능합니다.")
    
    # 시간별 날씨 정보 조회
    try:
        weather_data = await get_hourly_forecast(lat, lon, hours)
    except Exception as e:
        logger.error(f"시간별 날씨 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    if not weather_data:
        logger.error(f"날씨 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    # 시간별 대기질 정보 조회
    try:
        airquality_data = await get_hourly_air_quality(lat, lon, hours)
    except Exception as e:
        logger.error(f"시간별 대기질 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="대기질 정보를 찾을 수 없습니다.")

    weather_forecasts = weather_data.get("forecasts", [])
    air_forecasts = airquality_data.get("forecasts", [])
    
    air_forecast_map = {}
    for air_forecast in air_forecasts:
        key = f"{air_forecast.get('base_date', '')}_{air_forecast.get('base_time', '')}"
        air_forecast_map[key] = air_forecast
    
    combined_forecasts = []
    
    for weather in weather_forecasts:
        base_date = weather.get("base_date", "")
        base_time = weather.get("base_time", "")
        
        # 대기질 데이터 매핑 키
        key = f"{base_date}_{base_time}"
        
        # 해당 시간의 대기질 데이터 찾기
        air_quality = air_forecast_map.get(key, None)

        # 산책지수 데이터 생성
        combined_data = {
            "base_date": base_date,
            "base_time": base_time,
            "weather": {
                "temperature": weather.get("temperature"),
                "precipitation_type": weather.get("precipitation_type"),
                "sky_condition": weather.get("sky_condition")
            }
        }
        
        # 대기질 정보 추가
        if air_quality:
            pm10_grade = air_quality.get("pm10_grade")
            pm25_grade = air_quality.get("pm25_grade")

            combined_data["air_quality"] = {
                "pm10_grade": pm10_grade,
                "pm25_grade": pm25_grade,
                "air_quality_grade": calculate_air_quality_score_avg(pm10_grade, 0, pm25_grade, 0, air_quality_type),
            }
        else:
            # 대기질 정보가 없는 경우 기본값 사용
            combined_data["air_quality"] = {
                "pm10_grade": 0,
                "pm25_grade": 0,
                "air_quality_grade": 0           
            }
            
        # 산책 적합도 점수 계산
        try:
            walkability_data = walkability_calculator.calculate_walkability_score(
                temperature=combined_data["weather"]["temperature"],
                pm10_grade=combined_data["air_quality"]["pm10_grade"],
                pm10_value=0,
                pm25_grade=combined_data["air_quality"]["pm25_grade"],
                pm25_value=0,
                precipitation_type=combined_data["weather"]["precipitation_type"],
                sky_condition=combined_data["weather"]["sky_condition"],
                dog_size=dog_size,
                air_quality_type=air_quality_type
            )
            combined_data["walkability"] = {
                "score": walkability_data.get("walkability_score"),
                "grade": walkability_data.get("walkability_grade")
            }
        except Exception as e:
            logger.error(f"산책 적합도 점수 계산 실패: {str(e)}")
            combined_data["walkability_score"] = {
                "score": 50  # 중간 값으로 기본 설정
            }
       
        combined_forecasts.append(combined_data)
    
    result = {
        "forecasts": combined_forecasts
    }
    
    return result

async def get_walkability_weekly(
    lat: float, 
    lon: float, 
    days: int = 7,
    dog_size: str = "medium", 
    sensitive_groups: list = None,
    air_quality_type: str = "korean") -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param days: 일자 (1~7)
    :param dog_size: 견종 크기 (small/medium/large)
    :param air_quality_type: 대기질 기준 (korean/who)
    :param sensitivities: 민감군 목록 (쉼표로 구분)
    :return: 현재 날씨 정보
    """

    if(days > 7):
        logger.error(f"일자 조회 오류: {days}일은 최대 7일까지만 가능합니다.")
        raise HTTPException(status_code=400, detail="최대 7일까지만 조회 가능합니다.")

    # 시간별 날씨 정보 조회
    try:
        weather_data = await get_weekly_forecast(lat, lon, days)
    except Exception as e:
        logger.error(f"주간별 날씨 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    if not weather_data:
        logger.error(f"날씨 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    # 시간별 대기질 정보 조회
    try:
        airquality_data = await get_weekly_air_quality(lat, lon, air_quality_type, days)
    except Exception as e:
        logger.error(f"주간별 대기질 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="대기질 정보를 찾을 수 없습니다.")
    
    if not airquality_data:
        logger.error(f"대기질 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="대기질 정보를 찾을 수 없습니다.")
    
    weather_forecasts = weather_data.get("forecasts", [])
    air_forecasts = airquality_data.get("forecasts", [])
    
    air_forecast_map = {}
    for air_forecast in air_forecasts:
        key = air_forecast.get('base_date', '')
        air_forecast_map[key] = air_forecast
    
    combined_forecasts = []
    
    for weather in weather_forecasts:
        base_date = weather.get("base_date", "")
        
        # 대기질 데이터 매핑 키
        key = base_date
        
        # 해당 시간의 대기질 데이터 찾기
        air_quality = air_forecast_map.get(key, None)
        
        # 산책지수 데이터 생성
        min_temperature = weather.get("min_temperature")
        max_temperature = weather.get("max_temperature")
        combined_data = {
            "base_date": base_date,
            "weather": {
                "min_temperature": min_temperature,
                "max_temperature": max_temperature,
                "sky_condition": weather.get("sky_condition"),
                "precipitation_type": weather.get("precipitation_type")
            }
        }
        
        # 대기질 정보 추가
        air_quality_score = air_quality.get("air_quality_score")
        if air_quality:    
            combined_data["air_quality"] = {
                    "air_quality_grade": air_quality_score
            }
        
        # 산책 적합도 점수 계산
        # 최저 최고 기온에 따라 산책 적합도 산출
        try:
            min_temp_result = _walkability_calculator(
                min_temperature, 
                0, 0, air_quality_score, 0,
                combined_data["weather"], 
                dog_size, 
                air_quality_type)
            max_temp_result = _walkability_calculator(
                max_temperature, 
                0, 0, air_quality_score, 0,
                combined_data["weather"], 
                dog_size, 
                air_quality_type)

            combined_data["walkability"] = {
                'min_temperature': min_temp_result,
                'max_temperature': max_temp_result
            }
        except Exception as e:
            logger.error(f"산책 적합도 점수 계산 실패: {str(e)}")
            combined_data["walkability_score"] = {
                "score": 50  # 중간 값으로 기본 설정
            }
       
        combined_forecasts.append(combined_data)
        
    result = {
        "forecasts": combined_forecasts
    }
    
    return result

async def get_walkability_current_detail(
    lat: float, 
    lon: float) -> Dict[str, Any]:
    
    # 현재 날씨 상세 정보 조회
    fields = ["temperature", "humidity", "wind_speed", "rainfall"]
    try:
        weather_data = await get_ultra_short_forecast(lat, lon, fields)
    except Exception as e:
        logger.error(f"현재 날씨 상세 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="현재 날씨 정보를 찾을 수 없습니다.")
    
    if not weather_data:
        logger.error(f"현재 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="현재 날씨 정보를 찾을 수 없습니다.")

    # 오늘 일출 일몰 시간 조회
    try:
        astronomy_data = await get_sunrise_sunset(lat, lon)
    except Exception as e:
        logger.error(f"일출/일몰 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="천문 정보를 찾을 수 없습니다.")
    
    if not astronomy_data:
        logger.error(f"일출/일몰 정보 조회 실패: lat={lat}, lon={lon}")
        raise HTTPException(status_code=404, detail="천문 정보를 찾을 수 없습니다.")

    weather_data["sunrise"] = astronomy_data["sunrise"]
    weather_data["sunset"] = astronomy_data["sunset"]

    # 체감 온도
    weather_data["apparent_temperature"] = calculate_apparent_temperature(
        temperature=weather_data["temperature"],
        humidity=weather_data["humidity"],
        wind_speed=weather_data["wind_speed"]
    )

    # 현재 자외선 지수 조회
    try:
        uv_data =  await get_weather_uvindex(lat, lon)
    except Exception as e:
        logger.error(f"자외선 지수 조회 실패: {str(e)}")
        raise HTTPException(status_code=404, detail="자외선 지수를 찾을 수 없습니다.")
    
    weather_data["uv_index"] = uv_data
    
    results = {
        "weather": weather_data
    }
    return {"forecasts": results}

def _walkability_calculator(
    temperature: float,
    pm10_grade: int,
    pm10_value: int,
    pm25_grade: int,
    pm25_value: int,
    weather_data: Dict[str, Any],
    dog_size: str = "medium",
    air_quality_type: str = "korean"
    ) -> Dict[str, Any]:        
        return walkability_calculator.calculate_walkability_score(
            temperature=temperature,
            pm10_grade=pm10_grade,
            pm10_value=pm10_value,
            pm25_grade=pm25_grade,
            pm25_value=pm25_value,
            precipitation_type=weather_data.get("precipitation_type"),
            sky_condition=weather_data.get("sky_condition"),
            dog_size=dog_size,
            air_quality_type=air_quality_type
        )