from datetime import datetime
import sys
from typing import List, Optional, Dict, Any
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