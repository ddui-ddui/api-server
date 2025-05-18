from typing import Any, Dict

from fastapi import HTTPException
from app.services.weather_service import get_hourly_forecast
from app.services.air_quality import get_hourly_air_quality


async def get_walkability_houly(lat: float, 
    lon: float, 
    region: str, 
    hours: int = 12, 
    dog_size: str = "medium", 
    sensitive_groups: list = None) -> Dict[str, Any]:
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
    # 대기질 정보는 하루에 4번 제공함 
    # 그래서 데이터가 시간별이라기 보단 오전 오후 데이터라고 보면 편함
    airquality_data = await get_hourly_air_quality(lat, lon, region)
    
    if not airquality_data:
        raise HTTPException(status_code=404, detail="대기질 정보를 찾을 수 없습니다.")
    
    weather_forecasts = weather_data.get("forecasts", [])
    air_forecasts = airquality_data.get("forecasts", [])
    
    air_forecast_map = {}
    for air_forecast in air_forecasts:
        # 날짜와 시간을 키로 사용
        key = f"{air_forecast.get('forecast_date')}_{air_forecast.get('forecast_time')}"
        air_forecast_map[key] = air_forecast
    
    combined_forecasts = []
    
    for weather in weather_forecasts:
        forecast_date = weather.get("forecast_date", "")
        forecast_time = weather.get("forecast_time", "")
        
        # 대기질 데이터 매핑 키
        key = f"{forecast_date}_{forecast_time}"
        
        # 해당 시간의 대기질 데이터 찾기
        air_quality = air_forecast_map.get(key, None)
        
        # 산책지수 데이터 생성
        combined_data = {
            "forecast_date": forecast_date,
            "forecast_time": forecast_time,
            "weather": {
                "temperature": weather.get("temperature"),
                "precipitation_type": weather.get("precipitation_type"),
                "precipitation_probability": weather.get("precipitation_probability"),
                "sky_condition": weather.get("sky_condition")
            }
        }
        
        # 대기질 정보 추가
        if air_quality:
            combined_data["air_quality"] = {
                "pm10_grade": air_quality.get("pm10_grade"),
                "pm25_grade": air_quality.get("pm25_grade"),
                "air_quality_grade": air_quality.get("air_quality_grade")
            }
        else:
            # 대기질 정보가 없는 경우 기본값 사용
            combined_data["air_quality"] = {
                "pm10_grade": 0,
                "pm25_grade": 0,
                "air_quality_grade": 0
            }
        
        combined_forecasts.append(combined_data)
    
    result = {
        "region": region,
        "current_time": weather_data.get("current_time", ""),
        "base_time": weather_data.get("base_time_formatted", ""),
        "forecasts": combined_forecasts
    }
    
    return result