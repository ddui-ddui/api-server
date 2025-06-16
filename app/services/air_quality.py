from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from app.utils.convert_for_tm import convert_wgs84_to_katec
from app.core.config import settings
from urllib.parse import unquote
from app.common.http_client import make_request
from app.utils.airquality_calculator import calculate_air_quality_score
from app.utils.convert_for_region import convert_lat_lon_for_region
from app.config.logging_config import get_logger
logger = get_logger()


async def get_current_air_quality(lat: float, lon: float, air_quality_type: str = 'korean') -> Dict[str, Any]:
    """
    현재 공기질 정보 조회
    :param lat: 위도
    :param lon: 경도
    :return: 공기질 정보
    """
    
    # 가까운 측정소 찾기
    try:
        stations = await find_nearby_air_quality_station(lat, lon)
    except Exception as e:
        logger.error(f"측정소 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="측정소 조회 오류")

    if not stations:
        raise HTTPException(status_code=404, detail="근처에 공기질 측정소가 없습니다.")
    
    # 실시간 미세먼지 데이터 조회
    try:
        air_quality_data = await get_air_quality_data(stations, air_quality_type)
        return air_quality_data
    except Exception as e:
        logger.error(f"미세먼지 데이터 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="미세먼지 데이터 조회 오류")

async def find_nearby_air_quality_station(lat: float, lon: float) -> Optional[List]:
    """
    가까운 공기질 측정소를 찾기
    :param lat: 위도
    :param lon: 경도
    :return: 측정소명 리스트
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

        results = []
        for item in items:
            # 측정소명
            station_name = item.get("stationName", "")
            if not station_name:
                continue
            
            results.append(station_name)
        return results
    
    except Exception as e:
        logger.error(f"측정소 조회 오류: {str(e)}")
        return None

async def get_air_quality_data(stations: List[str], air_quality_type: str = 'korean') -> Dict[str, Any]:
    """
    측정소명 리스트로 미세먼지 데이터 조회 (순차적으로 시도)
    :param stations: 측정소명 리스트
    :param air_quality_type: 대기질 기준 (korean/who)
    :return: 미세먼지 데이터
    """
    # 미세먼지 API URL
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_STATION_URL}"
    
    # 모든 측정소에 대해 순차적으로 시도
    for station_name in stations:
        params = {
            "serviceKey": unquote(settings.GOV_DATA_API_KEY),
            "returnType": "json",
            "numOfRows": 1000,
            "pageNo": 1,
            "stationName": station_name,
            "dataTerm": "DAILY",
            "ver": "1.2"
        }
        
        try:
            response = await make_request(url=url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 응답 확인
            items = data.get("response", {}).get("body", {}).get("items", [])
            
            if not items:
                logger.info(f"측정소 '{station_name}': 데이터가 없음, 다음 측정소 시도")
                continue
            
            now = datetime.now()
            current_hour = now.hour
            today = now.date().strftime("%Y-%m-%d")
            target_datetime = f"{today} {current_hour:02d}:00"
            
            closest_item = None
            min_time_diff = float('inf')
            
            for item in items:
                # 측정 시간
                datatime = item.get("dataTime", "")
                if not datatime:
                    continue
                
                try:
                    measure_dt = datetime.strptime(datatime, "%Y-%m-%d %H:%M")
                    
                    if datatime == target_datetime:
                        closest_item = item
                        break
                    
                    # 가장 가까운 시간 찾기
                    time_diff = abs((now - measure_dt).total_seconds())
                    if time_diff < min_time_diff:
                        
                        # 통신 장애 확인
                        # 장애 시 과거 데이터로 대체
                        pm10_str = item.get("pm10Value", "")
                        pm25_str = item.get("pm25Value", "")
                        
                        pm10_valid = pm10_str and pm10_str != "-"
                        pm25_valid = pm25_str and pm25_str != "-"

                        if pm10_valid and pm25_valid:
                            min_time_diff = time_diff
                            closest_item = item
                except ValueError:
                    continue

            if not closest_item:
                logger.info(f"측정소 '{station_name}': 유효한 데이터가 없음, 다음 측정소 시도")
                continue
            
            # 미세먼지 데이터 검증
            pm10_str = closest_item.get("pm10Value", "")
            pm25_str = closest_item.get("pm25Value", "")
            
            # pm10Value나 pm25Value가 없거나 "-"인 경우 다음 측정소로
            if not pm10_str or pm10_str == "-" or not pm25_str or pm25_str == "-":
                logger.info(f"측정소 '{station_name}': PM10({pm10_str}) 또는 PM2.5({pm25_str}) 데이터가 유효하지 않음, 다음 측정소 시도")
                continue
            
            try:
                pm10 = int(pm10_str)
                pm25 = int(pm25_str)
            except ValueError:
                logger.info(f"측정소 '{station_name}': 미세먼지 값을 숫자로 변환할 수 없음, 다음 측정소 시도")
                continue
            
            # 유효한 데이터를 찾았으므로 결과 반환
            pm10_grade, pm25_grade = calculate_air_quality_score(pm10, pm25, air_quality_type)
            
            results = {
                "pm10_value": pm10,
                "pm10_grade": pm10_grade,
                "pm25_value": pm25,
                "pm25_grade": pm25_grade,
            }
            return results
            
        except Exception as e:
            logger.info(f"측정소 '{station_name}' 조회 중 오류 발생: {str(e)}, 다음 측정소 시도")
            continue
    
    # 모든 측정소를 시도했지만 유효한 데이터를 찾지 못한 경우
    logger.error(f"모든 측정소({len(stations)}개)에서 유효한 미세먼지 데이터를 찾을 수 없습니다.")
    raise HTTPException(
        status_code=404, 
        detail=f"해당 지역의 미세먼지 데이터를 찾을 수 없습니다. 시도한 측정소: {', '.join(stations)}"
    )
    

async def get_hourly_air_quality(lat: float, lon: float, hours: int = 12) -> Dict[str, Any]:
    """
    대기질 정보는 하루에 4번 제공함 
    그래서 데이터가 시간별이라기 보단 오전 오후 데이터라고 보면 편함
    조회 시간 기준으로 최신 데이터를 씀
    
    현재 날씨 정보 조회
    :param region: 지역명
    :param hour: 시간 (0-23)
    :return: 현재 날씨 정보
    """
    now = datetime.now()
    param_date = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    current_minute = now.minute
    region_data = convert_lat_lon_for_region(lat, lon)
    region = region_data.get("subregion")

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
            logger.info("대기질 예보 데이터가 없습니다.")
            return {'forecasts': []}
        
        forecast_time = [5, 11, 17, 23]
        closest_time = None
        
        for time in reversed(forecast_time):
            if time == current_hour and current_minute < 30:
                continue
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
        
            pm10_grade = convert_grade_to_value_for_hour(pm10_grade_str)
            pm25_grade = convert_grade_to_value_for_hour(pm25_grade_str)
                
            forecast_date_str = forecast_date.strftime("%Y%m%d")
            forecast_hour = f"{forecast_hour:02d}00"
            
            forecasts.append({
                "base_date": forecast_date_str,
                "base_time": forecast_hour,
                "pm10_grade": pm10_grade,
                "pm25_grade": pm25_grade
            })
            
        result = {
            "forecasts": forecasts
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대기질 데이터 처리 오류: {str(e)}")
    
async def get_weekly_air_quality(lat: float, lon: float, air_quality_type: str, days: int = 7) -> Dict[str, Any]:
    """
    주간예보는 당일 조회하면 3일 뒤의 예보부터 3일치가 제공됨
    19일에 조회하면 22일 ~ 24일 예보가 제공됨
    그래서 조회일 기준으로 하루 이틀 뒤의 예보부터 최신화하면서 가져와야 함
    그런데 또 내일(예를 들어 20일)부터는 조회가 안됨. 
    사실상 조회할 수 있는 날은 5일치가 최대임.
    7일로 조회할 경우 마지막 날의 데이터 반복처리
    에어코리아의 데이터가 최대 5일까지 정확도가 쓸만하다고 한다.
    그래서 그러는거 같음
    
    현재 날씨 정보 조회
    :param lat: 위도
    :param lon: 경도
    :param air_quality_type: 대기질 기준 (korean/who)
    :param days: 날짜 (1~7)
    :return: 현재 날씨 정보
    """
    if days > 7:
        raise HTTPException(status_code=400, detail="최대 7일까지만 조회 가능합니다.")
    
    now = datetime.now()
    today = now.date()
    start_date = today - timedelta(days=3)
    range_days = 3
    region = convert_lat_lon_for_region(lat, lon).get("subregion", "")
    
    
    # 주간 예보 기준 날짜 배열 생성
    dates = {}
    for i in range(1, days + 1):
        target_date = today + timedelta(days=i)
        date_str = target_date.strftime("%Y%m%d")
        dates[date_str] = None
        
    for i in range(range_days):
        params = {
            "serviceKey": unquote(settings.GOV_DATA_API_KEY),
            "returnType": "json",
            "pageNo": 1,
            "numOfRows": 100,
            "searchDate": start_date.strftime("%Y-%m-%d"),
        }
        start_date += timedelta(days=1)
    
        url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_WEEKLY_URL}"
        
        response = await make_request(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", [])
        
        if not items:
            continue
        
        item = items[0]
        date_fields = [
            ("frcstOneDt", "frcstOneCn"),
            ("frcstTwoDt", "frcstTwoCn"),
            ("frcstThreeDt", "frcstThreeCn"),
            ("frcstFourDt", "frcstFourCn")
        ]
        
        for date_field, forecast_field in date_fields:
            forecast_date = item.get(date_field, "")
            forecast_value = item.get(forecast_field, "")
            
            if not forecast_date or not forecast_value:
                continue
            
            # 날짜 형식 변환
            forecast_date_formatted = forecast_date.replace("-", "")
            if forecast_date_formatted in dates:
                value = parse_region_data(forecast_value, region)
                grade = convert_grade_to_value_for_week(value, air_quality_type)
                dates[forecast_date_formatted] = grade
    
    # 결과처리 및 5일 이후의 데이터는 마지막 데이터로 맵핑
    forecasts = []
    last_grade = None
    for date_str, grade in sorted(dates.items()):
        if grade is None:
            grade = last_grade
        else:
            last_grade = grade
            
        grade = grade if grade is not None else 2 # 혹시나 값이 없을 경우 보통으로 처리
        
        forecasts.append({
            "base_date": date_str,
            "air_quality_score": grade
        })
        
    
    return {'forecasts': forecasts}
    
    
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

def convert_grade_to_value_for_hour(grade):
    if grade == "좋음":
        return 1
    elif grade == "보통":
        return 2
    elif grade == "나쁨":
        return 3
    elif grade == "매우나쁨":
        return 4
    return 0

def convert_grade_to_value_for_week(grade: str, air_quality_type: str) -> int:
    """
    기상청 문서 기준
    초미세먼지 일평균 농도 "낮음"은 PM2.5 농도 0∼35 ㎍/㎥이며, "높음"은 PM2.5 농도 36 ㎍/㎥ 이상입니다.
    :param grade: 등급
    :return: 등급 점수
    """
    # 대기질 기준 설정
    standard = f"{air_quality_type}_standard" if air_quality_type in ["korean", "who"] else "korean_standard"
    
    if standard == "korean_standard":
        if grade == "낮음": # 좋음 수준으로 반환
            return 2
        elif grade == "높음": # 나쁨 수준으로 반환
                return 3
    elif standard == "who_standard":
        if grade == "낮음":
            return 2 # 보통 수준으로 반환
        elif grade == "높음":
            return 5 # 나쁨 수준으로 반환
    
        