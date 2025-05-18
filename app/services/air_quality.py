from datetime import date, datetime, timedelta
import sys
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from app.utils.convert_for_tm import convert_wgs84_to_katec
from app.core.config import settings
from urllib.parse import unquote
from app.common.http_client import make_request


async def get_air_quality_current(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    현재 공기질 정보 조회
    :param lat: 위도
    :param lon: 경도
    :return: 공기질 정보
    """
    
    # 가까운 측정소 찾기
    station = await find_nearby_air_quality_station(lat, lon)
    
    if not station:
        return None
    
    # 측정소명
    station_name = station.get("stationName", "")
    
    # 미세먼지 데이터 조회
    air_quality_data = await get_air_quality_data(station_name)
    
    return air_quality_data

async def find_nearby_air_quality_station(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    가까운 공기질 측정소를 찾기
    """
    
    tmx, tmy = convert_wgs84_to_katec(lat, lon)

    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_NEARSATIONS_URL}"
    
    params = {
        "serviceKey": unquote(settings.GOV_DATA_API_KEY),
        "returnType": "json",
        "tmX": tmx,
        "tmY": tmy,
        "ver": "1.1"
    }
    
    try:
        response = await make_request(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # 응답 확인
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return None
        
        # 가장 가까운 측정소 (첫 번째 항목)
        return items[0]
    
    except Exception as e:
        print(f"측정소 조회 오류: {str(e)}")
        return None

async def get_air_quality_data(station_name: str) -> List[Dict[str, Any]]:
    """
    측정소명으로 미세먼지 데이터 조회
    :param station_name: 측정소명
    :return: 미세먼지 데이터 리스트
    """
    # 미세먼지 API URL
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_STATION_URL}"
    
    params = {
        "serviceKey": unquote(settings.GOV_DATA_API_KEY),
        "returnType": "json",
        "stationName": station_name,
        "dataTerm": "DAILY",
        "ver": "1.2",
        "numOfRows": 1000
    }
    
    try:
        response = await make_request(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # 응답 확인
        items = data.get("response", {}).get("body", {}).get("items", [])
        
        # if not items:
        #     return []
        
        # 데이터 정리
        result = []
        # for item in items:
        #     # 측정 시간
        #     datatime = item.get("dataTime", "")
        #     if not datatime:
        #         continue
                
        #     try:
        #         measure_dt = datetime.strptime(datatime, "%Y-%m-%d %H:%M")
        #     except ValueError:
        #         continue
                
        #     # 미세먼지(PM10)
        #     pm10_str = item.get("pm10Value", "")
        #     try:
        #         pm10 = int(pm10_str) if pm10_str and pm10_str != "-" else 0
        #     except ValueError:
        #         pm10 = 0
                
        #     # 초미세먼지(PM2.5)
        #     pm25_str = item.get("pm25Value", "")
        #     try:
        #         pm25 = int(pm25_str) if pm25_str and pm25_str != "-" else 0
        #     except ValueError:
        #         pm25 = 0
                
        #     # 통합 대기질 등급
        #     # khaiGrade: 통합대기환경지수 등급 (1:좋음, 2:보통, 3:나쁨, 4:매우나쁨)
        #     khai_grade = item.get("khaiGrade", "")
        #     try:
        #         air_quality_grade = int(khai_grade) if khai_grade and khai_grade != "-" else 0
        #     except ValueError:
        #         air_quality_grade = 0
                
        #     air_quality_status = "정보없음"
        #     if air_quality_grade == 1:
        #         air_quality_status = "좋음"
        #     elif air_quality_grade == 2:
        #         air_quality_status = "보통"
        #     elif air_quality_grade == 3:
        #         air_quality_status = "나쁨"
        #     elif air_quality_grade == 4:
        #         air_quality_status = "매우나쁨"
                
            # result.append({
            #     "datetime": measure_dt,
            #     "pm10": pm10,
            #     "pm25": pm25,
            #     "air_quality_grade": air_quality_grade,
            #     "air_quality_status": air_quality_status
            # })
            
        return result
        
    except Exception as e:
        print(f"미세먼지 데이터 조회 오류: {str(e)}")
        return []
    

async def get_hourly_air_quality(lat: float, lon: float, region: str, hours: int = 12) -> Dict[str, Any]:
    """
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param hour: 시간 (0-23)
    :param region: 지역명
    :return: 현재 날씨 정보
    """
    now = datetime.now()
    param_date = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_HOURLY_URL}"
    
    params = {
        "serviceKey": unquote(settings.GOV_DATA_API_KEY),
        "returnType": "json",
        "pageNo": 1,
        "numOfRows": 1000,
        "searchDate": param_date,
        "InformCode": "PM10",
    }
    
    try:
        response = await make_request(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", [])
        
        if not items:
            raise HTTPException(status_code=404, detail="대기질 예보 데이터를 찾을 수 없습니다.")
        
        forecast_time = [5, 11, 17, 23]
        closest_time = None
        
        for time in reversed(forecast_time):
            if time <= current_hour:
                closest_time = time
                break
        if closest_time is None:
            closest_time = 23
            
        closest_time_str = f"{closest_time}시 발표"
        
        today_pm10 = None
        tomorrow_pm10 = None
        today_pm25 = None
        tomorrow_pm25 = None
        
        for item in items:
            if closest_time_str in item.get("dataTime", ""):
                if item.get("informCode") == "PM10":
                    if item.get("informData") == param_date:
                        today_pm10 = item
                    elif item.get("informData") == (now + timedelta(days=1)).strftime("%Y-%m-%d"):
                        tomorrow_pm10 = item
                elif item.get("informCode") == "PM25":
                    if item.get("informData") == param_date:
                        today_pm25 = item
                    elif item.get("informData") == (now + timedelta(days=1)).strftime("%Y-%m-%d"):
                        tomorrow_pm25 = item
        if not today_pm10 or not today_pm25:
            raise HTTPException(status_code=404, detail="오늘 대기질 예보 데이터를 찾을 수 없습니다.")
        
        forecasts = []
        start_hour = current_hour + 1
        
        for i in range(hours):
            forecast_hour = (start_hour + i) % 24
            forecast_date = now.date()
            
            if forecast_hour < start_hour and i > 0:
                forecast_date = now.date() + timedelta(days=1)
            
            if forecast_date == now.date():
                pm10_grade_str = parse_region_data(today_pm10.get("informGrade"), region)
                pm25_grade_str = parse_region_data(today_pm25.get("informGrade"), region)
            else:
                # 내일 데이터가 없으면 오늘 데이터로 대체
                if not tomorrow_pm10 or not tomorrow_pm25:
                    pm10_grade_str = parse_region_data(today_pm10.get("informGrade"), region)
                    pm25_grade_str = parse_region_data(today_pm25.get("informGrade"), region)
                else:
                    pm10_grade_str = parse_region_data(tomorrow_pm10.get("informGrade"), region)
                    pm25_grade_str = parse_region_data(tomorrow_pm25.get("informGrade"), region) 
        
            pm10_grade = convert_grade_to_value(pm10_grade_str)
            pm25_grade = convert_grade_to_value(pm25_grade_str)
            
            air_quality_grade = pm10_grade
                
            # 초미세먼지에 가중치 부여
            if pm25_grade > pm10_grade:
                air_quality_grade = pm25_grade
            elif pm25_grade >= 3:
                air_quality_grade = max(air_quality_grade, 3)
                
            forecast_date_str = forecast_date.strftime("%Y%m%d")
            forecast_hour = f"{forecast_hour:02d}00"
            
            forecasts.append({
                "forecast_date": forecast_date_str,
                "forecast_time": forecast_hour,
                "pm10_grade": pm10_grade,
                "pm25_grade": pm25_grade,
                "air_quality_grade": air_quality_grade,
            })
            
        result = {
            "forecasts": forecasts
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대기질 데이터 처리 오류: {str(e)}")
    
    
def parse_region_data(data_str, target_region):
    if not data_str:
        return "정보없음"
        
    regions = data_str.split(",")
    for region_data in regions:
        region_data = region_data.strip()
        if region_data.startswith(target_region) or target_region in region_data:
            parts = region_data.split(":")
            if len(parts) >= 2:
                return parts[1].strip()
    return "정보없음"

def convert_grade_to_value(grade):
    if grade == "좋음":
        return 1
    elif grade == "보통":
        return 2
    elif grade == "나쁨":
        return 3
    elif grade == "매우나쁨":
        return 4
    return 0