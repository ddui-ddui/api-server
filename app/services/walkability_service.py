from typing import Any, Dict

from fastapi import HTTPException
from app.services.weather_service import get_ultra_short_forecast, get_hourly_forecast, get_weekly_forecast
from app.services.air_quality import get_current_air_quality, get_hourly_air_quality, get_weekly_air_quality
from app.utils.walkability_calculator import WalkabilityCalculator
from app.utils.airquality_calculator import calculate_air_quality_score_avg

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
    weather_data = await get_ultra_short_forecast(lat, lon)
    if not weather_data:
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    results["weather"] = weather_data
    
    # 현재 대기질 정보 조회
    air_quality_data = await get_current_air_quality(lat, lon, air_quality_type)
    if not air_quality_data:
        raise HTTPException(status_code=404, detail="대기질 정보를 찾을 수 없습니다.")
    results["air_quality"] = air_quality_data
    
    return {"forecasts": results}

async def get_walkability_hourly(
    lat: float, 
    lon: float, 
    region: str, 
    hours: int = 12, 
    dog_size: str = "medium", 
    sensitive_groups: list = None,
    air_quality_type: str = "korean") -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param hour: 시간 (0-12)
    :param region: 지역명
    :return: 현재 날씨 정보
    """
    if(hours > 12):
        raise HTTPException(status_code=400, detail="최대 12시간까지만 조회 가능합니다.")
    
    # 시간별 날씨 정보 조회
    weather_data = await get_hourly_forecast(lat, lon, hours)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    # 시간별 대기질 정보 조회
    airquality_data = await get_hourly_air_quality(region, hours)

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
                "air_quality_score": calculate_air_quality_score_avg(pm10_grade, 0, pm25_grade, 0, air_quality_type),
            }
        else:
            # 대기질 정보가 없는 경우 기본값 사용
            combined_data["air_quality"] = {
                "pm10_grade": 0,
                "pm25_grade": 0,
                "air_quality_score": 0           
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
            print(f"산책 적합도 점수 계산 실패: {str(e)}")
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
    region: str, 
    days: int = 7,
    dog_size: str = "medium", 
    sensitive_groups: list = None,
    air_quality_type: str = "korean") -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param region: 지역명
    :return: 현재 날씨 정보
    """
    if(days > 7):
        raise HTTPException(status_code=400, detail="최대 7일까지만 조회 가능합니다.")

    # 시간별 날씨 정보 조회
    weather_data = await get_weekly_forecast(lat, lon, days)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail="날씨 정보를 찾을 수 없습니다.")
    
    # 시간별 대기질 정보 조회
    airquality_data = await get_weekly_air_quality(region, air_quality_type, days)
    
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
                    "air_quality_score": air_quality_score
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
                'low': min_temp_result,
                'high': max_temp_result
            }
        except Exception as e:
            print(f"산책 적합도 점수 계산 실패: {str(e)}")
            combined_data["walkability_score"] = {
                "score": 50  # 중간 값으로 기본 설정
            }
       
        combined_forecasts.append(combined_data)
        
    result = {
        "forecasts": combined_forecasts
    }
    
    return result

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