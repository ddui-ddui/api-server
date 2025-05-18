from typing import Any, Dict

from fastapi import HTTPException
from app.services.weather_service import get_hourly_forecast
from app.services.air_quality import get_hourly_air_quality
from app.utils.walkability_calculator import WalkabilityCalculator
from app.utils.airquality_calculator import calculate_air_quality_score

# 산책 적합도 계산기
walkability_calculator = WalkabilityCalculator()

async def get_walkability_houly(lat: float, 
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
    # 대기질 정보는 하루에 4번 제공함 
    # 그래서 데이터가 시간별이라기 보단 오전 오후 데이터라고 보면 편함
    airquality_data = await get_hourly_air_quality(lat, lon, region)

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
                "precipitation_probability": weather.get("precipitation_probability"),
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
                "air_quality_score": calculate_air_quality_score(pm10_grade, 0, pm25_grade, 0, air_quality_type),
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
                precipitation_probability=combined_data["weather"]["precipitation_probability"],
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