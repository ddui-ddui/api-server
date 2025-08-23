import asyncio
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from app.utils.convert_for_tm import convert_wgs84_to_katec
from app.core.config import settings
from urllib.parse import unquote
from app.common.http_client import make_request
from app.utils.airquality_calculator import calculate_individual_air_quality_score
from app.utils.convert_for_region import convert_lat_lon_for_region
from app.services.cache_service import AirQualityCacheService
from app.models.air_quality import HourlyAirQualityCache, WeeklyAirQualityCache
from app.utils.airquality_calculator import convert_grade_to_value_for_hour, convert_grade_to_value_for_week
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
    except HTTPException as e:
        raise
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
        "returnType": "json",
        "tmX": tmx,
        "tmY": tmy,
        "ver": "1.1"
    }
    
    try:
        response = await make_request(url=url, params=params)
        data = response.json()
        
        # 응답 확인
        items = data.get("response", {}).get("body", {}).get("items", [])
        if not items:
            return None

        results = []
        print(items)
        for item in items:
            # 측정소명
            station_name = item.get("stationName", "")
            if not station_name:
                continue
            
            results.append(station_name)
        return results
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 측정소 조회 오류: {str(e)}")
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
            "returnType": "json",
            "numOfRows": 1000,
            "pageNo": 1,
            "stationName": station_name,
            "dataTerm": "DAILY",
            "ver": "1.2"
        }
        
        try:
            response = await make_request(url=url, params=params)
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
            pm10_grade, pm25_grade = calculate_individual_air_quality_score(pm10, pm25, air_quality_type)
            worse_grade = max(pm10_grade, pm25_grade)
            
            results = {
                "pm10_value": pm10,
                "pm10_grade": pm10_grade,
                "pm25_value": pm25,
                "pm25_grade": pm25_grade,
                "air_quality_grade": worse_grade,
            }
            return results
            
        except Exception as e:
            logger.info(f"측정소 '{station_name}' 조회 중 오류 발생: {str(e)}, 다음 측정소 시도")
            continue
    
    # 모든 측정소를 시도했지만 유효한 데이터를 찾지 못한 경우
    logger.error(f"모든 측정소({len(stations)}개)에서 유효한 미세먼지 데이터를 찾을 수 없습니다.")
    logger.error(f"기본값으로 반환합니다.")
    results = {
        "pm10_value": None,
        "pm10_grade": None,
        "pm25_value": None,
        "pm25_grade": None,
        "air_quality_grade": None,
        "is_error": True
    }
    return results

async def get_hourly_air_quality(lat: float, lon: float, hours: int = 12) -> Dict[str, Any]:
    cached_data = await AirQualityCacheService().get_hourly_cache()
    if cached_data:
        logger.info("캐시된 시간별 대기질 데이터를 반환합니다.")
        return process_air_quality_data(cached_data.forecasts, lat, lon, hours)
    else:
        logger.info("캐시된 시간별 대기질 데이터가 없습니다. API에서 조회합니다.")
        
        now = datetime.now()
        param_date = now.strftime("%Y-%m-%d")
        raw_data = await fetch_hourly_air_quality_raw(param_date)
        cache_data = HourlyAirQualityCache(
            forecasts=raw_data,
            cached_at=datetime.now().isoformat()
        )
        await AirQualityCacheService().set_hourly_cache(cache_data)
        
        return process_air_quality_data(raw_data, lat, lon, hours)
    
def process_air_quality_data(raw_data: Dict[str, Any], lat: float, lon: float, hours: int) -> Dict[str, Any]:
    """시간별 대기질 데이터 가공 (캐시/API 공통 사용)"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    region_data = convert_lat_lon_for_region(lat, lon)
    region = region_data.get("subregion")

    forecast_time = [5, 11, 17, 23]
    closest_time = None
    param_date = None

    if current_hour < 5 or (current_hour == 5 and current_minute < 30):
        closest_time = 23
        param_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # 현재 시간 기준으로 가장 최근 발표 시간 찾기
        for time in reversed(forecast_time):
            if time == current_hour and current_minute < 30:
                continue
            if time <= current_hour:
                closest_time = time
                break
        
        if closest_time is None:
            closest_time = 23
            param_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            param_date = now.strftime("%Y-%m-%d")

    items = raw_data.get("response", {}).get("body", {}).get("items", [])
    if not items:
        logger.info("대기질 예보 데이터가 없습니다.")
        return {'forecasts': []}
        
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
        
    return {"forecasts": forecasts}
    
async def get_hourly_air_quality_from_api(lat: float, lon: float, hours: int = 12) -> Dict[str, Any]:
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
    current_hour = now.hour
    current_minute = now.minute

    forecast_time = [5, 11, 17, 23]
    closest_time = None
    param_date = None

    if current_hour < 5 or (current_hour == 5 and current_minute < 30):
        closest_time = 23
        param_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # 현재 시간 기준으로 가장 최근 발표 시간 찾기
        for time in reversed(forecast_time):
            if time == current_hour and current_minute < 30:
                continue
            if time <= current_hour:
                closest_time = time
                break
        
        if closest_time is None:
            closest_time = 23
            param_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            param_date = now.strftime("%Y-%m-%d")
    
    raw_data = await fetch_hourly_air_quality_raw(param_date)
    return process_air_quality_data(raw_data, lat, lon, hours)

async def fetch_hourly_air_quality_raw(search_date: str) -> Dict[str, Any]:
    """
    시간별 대기질 원본 데이터 조회 (날짜만 필요)
    :param search_date: 조회 날짜 (YYYY-MM-DD)
    :return: API 원본 응답 데이터
    """
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_HOURLY_URL}"    
    params = {
        "returnType": "json",
        "pageNo": 1,
        "numOfRows": 1000,
        "searchDate": search_date,
        "InformCode": "PM10",
    }
    try:
        response = await make_request(url=url, params=params)
        data = response.json()
        return data
    except Exception as e:
        logger.error(f"시간별 대기질 원본 데이터 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="시간별 대기질 원본 데이터 조회 오류")
    
async def get_weekly_air_quality(lat: float, lon: float, air_quality_type: str, days: int = 7) -> Dict[str, Any]:
    if days > 7:
        raise HTTPException(status_code=400, detail="최대 7일까지만 조회 가능합니다.")
    
    cached_data = await AirQualityCacheService().get_weekly_cache()
    if cached_data:
        logger.info("캐시된 주간 대기질 데이터에서 지역별 데이터를 추출합니다.")
        # 캐시된 가공 데이터에서 사용자 지역만 추출
        return extract_region_data_from_cache(cached_data.forecasts, lat, lon, air_quality_type, days)
    else:
        logger.info("캐시된 주간 대기질 데이터가 없습니다. API에서 조회합니다.")
        
        # API에서 가공된 데이터 생성
        processed_forecasts = await process_weekly_air_quality_for_cache()
        
        # 가공된 데이터를 캐시에 저장
        cache_data = WeeklyAirQualityCache(
            forecasts=processed_forecasts,  # 가공된 전국 데이터 저장
            cached_at=datetime.now().isoformat()
        )
        await AirQualityCacheService().set_weekly_cache(cache_data)
        
        return extract_region_data_from_cache(processed_forecasts, lat, lon, air_quality_type, days)
    
async def get_weekly_air_quality_from_api(lat: float, lon: float, air_quality_type: str, days: int = 7) -> Dict[str, Any]:
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
        data = await fetch_weekly_air_quality_raw(search_date=start_date.strftime("%Y-%m-%d"))
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

        # 캐시가 없을 때 tps 줄이는 용도
        if i > 0:
            await asyncio.sleep(0.5)
    
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

def extract_region_data_from_cache(cached_forecasts: List[Dict], lat: float, lon: float, air_quality_type: str, days: int) -> Dict[str, Any]:
    """캐시된 전국 데이터에서 사용자 지역 데이터만 추출"""
    region = convert_lat_lon_for_region(lat, lon).get("subregion", "")
    
    results = []
    
    try:
        for i in range(min(days, len(cached_forecasts))):
            forecast = cached_forecasts[i]
            all_regions_data = forecast.get("all_regions_data", "")
            
            # 사용자 지역 데이터만 추출
            region_value = parse_region_data(all_regions_data, region)
            grade = convert_grade_to_value_for_week(region_value, air_quality_type)
            
            results.append({
                "base_date": forecast.get("base_date"),
                "air_quality_score": grade
            })
        
        return {"forecasts": results}
    except Exception as e:
        logger.error(f"캐시된 주간 대기질 데이터 처리 오류: {str(e)}")
        logger.error(f"요청된 위도 경도: ({lat}, {lon}), 지역: {region}")
        raise HTTPException(status_code=500, detail="캐시된 주간 대기질 데이터 처리 오류")

async def process_weekly_air_quality_for_cache() -> List[Dict[str, Any]]:
    """
    주간별 대기질 데이터 가공 (캐시 저장용 - 전국 지역 파싱, 7일치 완성)
    """
    now = datetime.now()
    today = now.date()
    start_date = today - timedelta(days=3)
    range_days = 3
    
    # 7일치 날짜 배열 생성
    dates = {}
    for i in range(1, 8):  # 1~7일
        target_date = today + timedelta(days=i)
        date_str = target_date.strftime("%Y%m%d")
        dates[date_str] = None
        
    # 3번 API 호출해서 최신 데이터로 덮어쓰기
    for i in range(range_days):
        search_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        data = await fetch_weekly_air_quality_raw(search_date)
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
                dates[forecast_date_formatted] = {
                    "base_date": forecast_date_formatted,
                    "all_regions_data": forecast_value
                }

        # TPS 조절
        if i > 0:
            await asyncio.sleep(0.5)
    
    forecasts = []
    last_forecast = None
    
    for date_str in sorted(dates.keys()):
        if dates[date_str]:
            forecast = dates[date_str]
            last_forecast = forecast
        else:
            if last_forecast:
                forecast = {
                    "base_date": date_str,
                    "all_regions_data": last_forecast["all_regions_data"]
                }
            else:
                forecast = {
                    "base_date": date_str,
                    "all_regions_data": "정보없음"
                }
        
        forecasts.append(forecast)
    
    return forecasts

async def fetch_weekly_air_quality_raw(search_date: str) -> Dict[str, Any]:
    """
    주간별 대기질 원본 데이터 조회 (날짜만 필요)
    :param search_date: 조회 날짜 (YYYY-MM-DD)
    :return: API 원본 응답 데이터
    """
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_AIRQUALITY_WEEKLY_URL}"
    
    params = {
        "returnType": "json",
        "pageNo": 1,
        "numOfRows": 100,
        "searchDate": search_date,
    }
    
    response = await make_request(url=url, params=params)
    data = response.json()
    return data
    
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
    
        