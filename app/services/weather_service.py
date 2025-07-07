import json
from fastapi import HTTPException
from app.config.redis_config import get_redis_client
from app.core.config import settings
from typing import Any, Dict, List
from datetime import datetime, timedelta
from app.utils.cache_utils import calculate_ttl_to_next_mid_forecast, calculate_ttl_to_next_short_forecast
from app.utils.convert_for_grid import mapToGrid
from app.common.http_client import make_request
from urllib.parse import unquote
from app.utils.weather_format_utils import convert_weather_condition, parse_rainfall
from app.utils.convert_for_region import convert_grid_to_region, convert_lat_lon_for_region, convert_lat_lon_to_region_id
from app.config.logging_config import get_logger
logger = get_logger()

async def get_previous_weather(lat: float, lon: float, current_date: str, current_time: str) -> float:
    """
    어제 날씨 정보 조회
    :param station_id: 관측소 ID
    :param prev_date: 어제 날짜 (YYYY-MM-DD 형식)
    :param prev_time: 어제 시간 (HHMM 형식)
    :return: 어제 날씨 정보
    """
    stations = convert_lat_lon_to_region_id(lat, lon)

    prev_date = (datetime.strptime(current_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_time = (datetime.strptime(current_time, "%H%M")).strftime("%H:%M")

    prev_datetime = prev_date + " " + prev_time
    params_date = prev_date.replace("-", "")

    for station in stations:
        try:
            params = {
                "numOfRows": 24,
                "dataType": "JSON",
                "dataCd": "ASOS",
                "dateCd": "HR",
                "startDt": params_date,
                "startHh": "00",
                "endDt": params_date,
                "endHh": "23",
                "stnIds": station["reg_id"],
            }
        
            url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_SEARCH_PREV_URL}"
            response = await make_request(url=url, params=params)
            data = response.json()

            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

            if not items:
                logger.info(f"관측소 {station['reg_id']}: 데이터가 없습니다.")
                continue
            
            yesterday_temp = None
            for item in items:
                item_time = item.get("tm", "")
                if item_time == prev_datetime:
                    temp_value = item.get("ta")
                    if temp_value and temp_value.strip() != "":
                        try:
                            yesterday_temp = float(temp_value)
                            break
                        except (ValueError, TypeError):
                            continue
            
            if yesterday_temp is None:
                logger.info(f"관측소 {station['reg_id']}: 정확한 시간 데이터 없음, 가장 가까운 시간 사용")
                
                target_hour = int(prev_time.split(":")[0])
                closest_temp = None
                min_hour_diff = float('inf')
                
                for item in items:
                    temp_value = item.get("ta")
                    item_time = item.get("tm", "")
                    
                    if temp_value and temp_value.strip() != "" and item_time:
                        try:
                            temp = float(temp_value)
                            # 시간 추출
                            time_part = item_time.split(" ")[1] if " " in item_time else "00:00:00"
                            item_hour = int(time_part.split(":")[0])
                            
                            hour_diff = abs(target_hour - item_hour)
                            if hour_diff < min_hour_diff:
                                min_hour_diff = hour_diff
                                closest_temp = temp
                        except (ValueError, TypeError, IndexError):
                            continue
                
                yesterday_temp = closest_temp


            if yesterday_temp is not None:
                return yesterday_temp
            else:
                logger.info(f"관측소: {station['reg_id']} 지역: {station['region']} 기상관측소: {station['meteorological']}: 유효한 온도 데이터 없음")
                continue
            
        except HTTPException as e:
            logger.warning(f"관측소 {station['reg_id']} ({station['region']}) API 오류: {e.detail}")
            continue
        except Exception as e:
            logger.warning(f"관측소 {station['reg_id']} ({station['region']}) 예상치 못한 오류: {str(e)}")
            continue

    logger.error("모든 관측소에서 어제 온도 데이터를 가져올 수 없습니다.")
    return None
     

async def get_ultra_short_forecast(lat: float, lon: float, fields: List[str] = None) -> Dict[str, Any]:
    """
    초단기 예보 조회
    :param nx: 예보지점 X 좌표
    :param ny: 예보지점 Y 좌표
    :return: 초단기 예보 데이터
    """

    nx, ny = mapToGrid(lat, lon)
    
    # Current time
    now = datetime.now()
    if now.minute < 45:
        now = now - timedelta(hours=1)

    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")
    current_fcst_time = now.strftime("%H%M")


    # Request URL
    params = {
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_ULTRA_SHORT_URL}"
    
    try:
            response = await make_request(url=url, params=params)
            data = response.json()
            
            # 결과 데이터 추출
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if not items:
                raise HTTPException(status_code=404, detail="날씨 데이터를 찾을 수 없습니다.")
            
            forecast_times = sorted(set(item.get("fcstTime") for item in items))
            closest_time = min(forecast_times, key=lambda x: abs(int(x) - int(current_fcst_time)))

            # 초 단기예보 카테고리
            # 코드 : T1H(기온), RN1(1시간 강수량), SKY(하늘상태), REH(습도), PTY(강수형태), LGT(낙뢰), VEC(풍향), WSD(풍속)
            weather_data = {}
            for item in items:
                category = item.get("category")
                fcst_time = item.get("fcstTime")
                fcst_value = item.get("fcstValue")

                if fcst_time == closest_time:
                    weather_data[category] = fcst_value

            all_data = {
                "temperature": float(weather_data.get("T1H", 0)),
                "sky_condition": int(weather_data.get("SKY", 0)),
                "humidity": int(weather_data.get("REH", 0)),
                "wind_direction": int(weather_data.get("VEC", 0)),
                "wind_speed": float(weather_data.get("WSD", 0)),
                "rainfall": parse_rainfall(weather_data.get("RN1", 0)),
                "precipitation_type": int(weather_data.get("PTY", 0)),
                "lightning": False if int(weather_data.get("LGT", 0)) == 0 else True,
            }

            # 최고/최저 기온 조회
            if fields is None or "min_temperature" in fields or "max_temperature" in fields:
                try:
                    daily_temperature = await get_daily_temperature_range(nx, ny)
                    all_data['min_temperature'] = float(daily_temperature.get("min_temperature", 0))
                    all_data['max_temperature'] = float(daily_temperature.get("max_temperature", 0))
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"최고/최저 기온 조회 중 예상치 못한 오류: {str(e)}")
                    raise HTTPException(status_code=500, detail="최고/최저 기온 조회 오류")

            # 전날 날씨 데이터 조회 및 기온 차이 계산
            if fields is None or "previous_temperature" in fields or "temperature_difference" in fields:
                try:
                    prev_weather = await get_previous_weather(lat, lon, base_date, base_time)
                except HTTPException as e:
                    raise
                except Exception as e:
                    logger.error(f"전날 날씨 조회 중 오류: {str(e)}")
                    raise HTTPException(status_code=500, detail="전날 날씨 조회 오류")
                
                current_temperature = all_data['temperature']

                if prev_weather is not None:                    
                    diff_temperature = round(current_temperature - prev_weather, 1)
                    all_data['prev_weather'] = prev_weather
                    all_data['temperature_difference'] = diff_temperature
                else: 
                    current_temperature = all_data['temperature']
                    all_data['prev_weather'] = None
                    all_data['temperature_difference'] = None
                    
            if fields is None:
                result = {
                    "temperature": current_temperature,
                    "prev_temperature": prev_weather,
                    "temperature_difference": diff_temperature,
                    "sky_condition": int(weather_data.get("SKY", 0)),
                    "precipitation_type": int(weather_data.get("PTY", 0)),
                    "min_temperature": float(daily_temperature.get("min_temperature", 0)),
                    "max_temperature": float(daily_temperature.get("max_temperature", 0)),
                }
                return result
            else:
                return {field: all_data[field] for field in fields if field in all_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"초단기 예보 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="초단기 날씨 서비스 오류")

async def get_hourly_forecast(lat: float, lon: float, hours: int = 12) -> Dict[str, Any]:
    """
    시간별 예보 조회 (최대 12시간)
    :param lat: 위도
    :param lon: 경도
    :param hours: 조회할 시간 수 (기본값: 12시간)
    :return: 시간별 예보 데이터 리스트
    """
    nx, ny = mapToGrid(lat, lon)

    # 캐시 조회
    cache_key = f"weather:hourly:{nx}:{ny}:{hours}"
    try:
        redis = await get_redis_client()
        cached_data = await redis.get(cache_key)
        if cached_data:
            logger.info(f"캐시에서 시간별 날씨 예보 조회: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"캐시 조회 실패, 새로운 데이터 조회: {str(e)}")
    
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    current_time = now.strftime("%H%M")
    current_date = now.strftime("%Y%m%d")

    
    # 예보 기준 시간 설정
    # 기상청은 3시간 단위로 예보를 제공함.
    current_hour = now.hour
    base_times = [2, 5, 8, 11, 14, 17, 20, 23]

    # 현재 시간에 가장 가까운 예보 기준 시간 설정
    base_time = None
    for t in reversed(sorted(base_times)):
        if t <= current_hour:
            base_time = t
            break
    
    
    if base_time is None:
        yesterday = now - timedelta(days=1)
        base_date = yesterday.strftime("%Y%m%d")
        base_time = 23
    
    base_time = f"{base_time:02d}00"
    
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_SHORT_URL}"
    
    params = {
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    try:
        response = await make_request(url=url, params=params)
        data = response.json()
        
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        if not items:
            raise HTTPException(status_code=404, detail="날씨 데이터를 찾을 수 없습니다.")
        
        # 시간대별로 데이터 그룹화
        forecasts_by_time = {}
        for item in items:
            fcst_date = item.get("fcstDate")
            fcst_time = item.get("fcstTime")            
            key = f"{fcst_date}-{fcst_time}"
            
            if key not in forecasts_by_time:
                forecasts_by_time[key] = {
                    "forecast_date": fcst_date,
                    "forecast_time": fcst_time
                }
            
            category = item.get("category")
            value = item.get("fcstValue")
            
            if category == "TMP":  # 기온
                forecasts_by_time[key]["temperature"] = float(value)
            elif category == "PTY":  # 강수형태 (0:없음, 1:비, 2:비/눈, 3:눈, 4:소나기)
                forecasts_by_time[key]["precipitation_type"] = int(value)
            elif category == "SKY":  # 하늘상태 (1:맑음, 3:구름많음, 4:흐림)
                forecasts_by_time[key]["sky_condition"] = int(value)
            elif category == "POP":  # 강수확률
                forecasts_by_time[key]["precipitation_probability"] = int(value)
            # elif category == "PCP": # 강수량
            #     amount = float(value)
            #     if amount >= 0.1 and amount < 1.0:
            #         forecasts_by_time[key]["precipitation_amount"] = f"{1}mm 미만"
            #     elif amount >= 1.0 and amount < 30.0:
            #         forecasts_by_time[key]["precipitation_amount"] = f"{value}mm"
            #     elif amount >= 30.0 and amount < 50.0:
            #         forecasts_by_time[key]["precipitation_amount"] = f"30mm~50mm"
            #     elif amount >= 50.0:
            #         forecasts_by_time[key]["precipitation_amount"] = f"50mm 이상"
        
        future_forecasts = {}
        for key, forecast in forecasts_by_time.items():
            fcst_date = forecast["forecast_date"]
            fcst_time = forecast["forecast_time"]
            
            if (fcst_date > current_date) or (fcst_date == current_date and fcst_time > current_time):
                future_forecasts[key] = forecast
        
        # 현재 시간부터 지정된 시간까지의 예보만 추출
        result_forecasts = []
        
        # 시간 정렬
        sorted_keys = sorted(future_forecasts.keys())
        count = 0
        for key in sorted_keys:
            forecast = forecasts_by_time[key]
            # 필수 필드 확인
            required_fields = ["temperature", "sky_condition", "precipitation_type", "precipitation_probability"]
        
            if all(field in forecast for field in required_fields):
                # 날짜 형식 정리
                fcst_date = forecast["forecast_date"]
                fcst_time = forecast["forecast_time"]
                forecast["base_date"] = fcst_date
                forecast["base_time"] = fcst_time
                result_forecasts.append(forecast)
                count += 1
                
                # 지정된 시간 수에 도달하면 중단
                if count >= hours:
                    break

        # 메타데이터 추가
        result = {
            "forecasts": result_forecasts
        }

        # 캐시 저장 (다음 단기예보 발표 시간까지)
        try:
            ttl_seconds = calculate_ttl_to_next_short_forecast()
            await redis.set(cache_key, json.dumps(result, default=str), ex=ttl_seconds)
            logger.info(f"시간별 날씨 예보 캐시에 저장: {cache_key}, TTL: {ttl_seconds}초")
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {str(e)}")
        
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시간별 예보 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="시간별 날씨 서비스 오류")
    
async def get_daily_temperature_range(nx: float, ny: float) -> Dict[str, Any]:
    """
    오늘의 최고/최저 기온 조회
    :param nx: 위도
    :param ny: 경도
    :return: 최고/최저 기온 데이터
    """
    
    # 현재 시간
    now = datetime.now()
    today = now.strftime("%Y%m%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y%m%d")
    
    # 단기예보는 매일 새벽 5시에 한 번만 발표
    current_hour = now.hour
    current_minute = now.minute
    
    # 0500에 바로 업데이트가 되지 않기 때문에 30분 보호
    if current_hour < 5 or (current_hour == 5 and current_minute < 30):
        yesterday = now - timedelta(days=1)
        base_date = yesterday.strftime("%Y%m%d")
        base_time = "0500"
    else:
        base_date = today
        base_time = "0500"
    
    # 단기예보 API URL
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_SHORT_URL}"

    params = {
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    
    try:
        response = await make_request(url=url, params=params)
        data = response.json()
        
        # 결과 데이터 추출
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            logger.error("단기예보 API에서 날씨 데이터를 찾을 수 없습니다.")
            raise HTTPException(status_code=404, detail="날씨 데이터를 찾을 수 없습니다.")
        
        # 오늘과 내일의 최고/최저 기온 찾기
        min_temp = None
        max_temp = None
        
        for item in items:
            fcst_date = item.get("fcstDate")
            category = item.get("category")
            value = item.get("fcstValue")
            
            # 오늘의 최고 기온과 내일의 최저 기온
            if (fcst_date == today and category == "TMX") or (fcst_date == tomorrow and category == "TMN"):
                if category == "TMN":
                    try:
                        min_temp = float(value)
                    except (ValueError, TypeError):
                        pass
                elif category == "TMX":
                    try:
                        max_temp = float(value)
                    except (ValueError, TypeError):
                        pass
        
        # 최고/최저 기온이 없으면 시간별 예보에서 계산
        if min_temp is None or max_temp is None:
            
            # 오늘의 시간별 예보에서 최고/최저 기온 계산
            today_temps = []
            for item in items:
                if item.get("fcstDate") == today and item.get("category") == "TMP":
                    try:
                        temp = float(item.get("fcstValue", 0))
                        today_temps.append(temp)
                    except (ValueError, TypeError):
                        pass
            
            if today_temps:
                if min_temp is None:
                    min_temp = min(today_temps)
                if max_temp is None:
                    max_temp = max(today_temps)
        
        # 결과 구성
        result = {
            "date": f"{today[:4]}-{today[4:6]}-{today[6:]}",
            "min_temperature": min_temp,
            "max_temperature": max_temp,
            "base_date": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]}",
            "base_time": f"{base_time[:2]}:{base_time[2:]}"
        }
        
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"최고/최저 기온 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="기온 조회 서비스 오류")
    
async def get_weekly_forecast(lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
    """
    내일부터 일주일간의 날씨 예보 조회 (수정된 버전)
    :param lat: 위도
    :param lon: 경도
    :return: 일주일 예보 데이터
    """
    # 격자 좌표 변환
    nx, ny = mapToGrid(lat, lon)

    cache_key = f"weather:weekly:{nx}:{ny}:{days}"
    
    # 캐시 조회
    try:
        redis = await get_redis_client()
        cached_data = await redis.get(cache_key)
        if cached_data:
            logger.info(f"캐시에서 주간 날씨 예보 조회: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"캐시 조회 실패, 새로운 데이터 조회: {str(e)}")
    
    # 현재 시간 기준
    now = datetime.now()
    today = now.date()
    
    # 단기예보 API로 데이터 가져오기 (최대 5일)
    try:
        short_forecasts = await get_short_range_forecast(nx, ny)
    except HTTPException as e:
        logger.error(f"단기예보 조회 오류: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=f"단기예보 조회 오류: {str(e.detail)}")
    
    # 중기예보 API로 나머지 데이터 가져오기
    # 현재 시간이 17시 이후인지에 따라 5일~10일 또는 4일~10일
    try:
        mid_forecasts = await get_mid_range_forecast(nx, ny)
    except HTTPException as e:
        logger.error(f"중기예보 조회 오류: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=f"중기예보 조회 오류: {str(e.detail)}")
    
    # 결과 합치기
    weekly_forecast = []
    
    # 1. 단기예보 처리 (내일~4/5일 후)
    max_short_days = 5  # 단기예보 최대 일수
    for i in range(1, max_short_days+1):  # 내일부터 5일 후까지
        target_date = today + timedelta(days=i)
        target_date_str = target_date.strftime("%Y%m%d")
        
        # 해당 날짜의 시간별 예보 추출
        day_forecasts = [f for f in short_forecasts if f.get("base_date") == target_date_str]
        
        if day_forecasts:
            # 온도 정보 찾기
            temps = [f.get("temperature") for f in day_forecasts if "temperature" in f]
            min_temp = min(temps) if temps else 0
            max_temp = max(temps) if temps else 0
            
            # 대표 시간대 찾기 (낮 시간대 중에서)
            noon_time = "1200"
            noon_forecast = next((f for f in day_forecasts if f.get("base_time") == noon_time), None)
            
            if noon_forecast is None and day_forecasts:
                # 정오 데이터가 없으면 낮 시간대 중 하나 선택
                daytime_forecasts = [f for f in day_forecasts if 
                                    f.get("base_time") >= "0900" and 
                                    f.get("base_time") <= "1800"]
                if daytime_forecasts:
                    noon_forecast = daytime_forecasts[len(daytime_forecasts)//2]  # 중간값
                else:
                    noon_forecast = day_forecasts[0]  # 첫 번째 값
            
            # 간소화된 날짜별 요약
            if noon_forecast:
                # 강수 형태와 하늘 상태 정보를 통합 처리
                sky_condition = noon_forecast.get("sky_condition", 0)
                precipitation_type = noon_forecast.get("precipitation_type", 0)
                
                day_summary = {
                    "base_date": target_date_str,
                    "min_temperature": min_temp,
                    "max_temperature": max_temp,
                    "sky_condition": sky_condition,
                    "precipitation_type": precipitation_type
                }
                
                weekly_forecast.append(day_summary)
    
    # 2. 중기예보 처리 (단기예보가 없는 날짜부터 7일 후까지)
    current_hour = now.hour
    mid_start_day = 5 if current_hour >= 17 else 4  # 18시 기준 발표는 5일부터, 6시 기준은 4일부터
    
    for i in range(mid_start_day, 8):  # 최대 7일까지만 (내일부터 7일)
        target_date = today + timedelta(days=i)
        target_date_str = target_date.strftime("%Y%m%d")
        
        # 이미 단기예보에서 추가한 날짜인지 확인
        existing_day = next((d for d in weekly_forecast if d.get("base_date") == target_date_str), None)

        # 중복 날짜가 아니고, 중기예보에 해당 날짜 데이터가 있는 경우
        if not existing_day:
            # 중기예보에서 해당 날짜 찾기
            day_forecast = next((f for f in mid_forecasts if f.get("base_date") == target_date_str), None)
            
            if day_forecast:
                # 중기예보와 단기예보의 형식을 일치시킴
                normalized_forecast = {
                    "base_date": day_forecast.get("base_date", ""),
                    "min_temperature": day_forecast.get("min_temperature", 0),
                    "max_temperature": day_forecast.get("max_temperature", 0),
                    "sky_condition": day_forecast.get("sky_condition", 0),
                    "precipitation_type": day_forecast.get("precipitation_type", 0)
                }
                weekly_forecast.append(normalized_forecast)
    
    # 날짜순 정렬
    weekly_forecast.sort(key=lambda x: x["base_date"])
    weekly_forecast = weekly_forecast[:days]

    result = {'forecasts': weekly_forecast}

    # 캐시 저장
    try:
        ttl_seconds = calculate_ttl_to_next_mid_forecast()
        await redis.set(cache_key, json.dumps(result, default=str), ex=ttl_seconds)
        logger.info(f"주간 날씨 예보 캐시에 저장: {cache_key}, TTL: {ttl_seconds}초")
    except Exception as e:
        logger.warning(f"캐시 저장 실패: {str(e)}")
    
    return result

# 단기예보(주간예보용)
async def get_short_range_forecast(nx: int, ny: int) -> List[Dict[str, Any]]:
    """단기예보 API로 상세 예보 데이터 조회"""
    # 현재 시간
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    
    # 예보 기준 시간 설정
    current_hour = now.hour
    base_times = [2, 5, 8, 11, 14, 17, 20, 23]
    
    # 현재 시간에 가장 가까운 예보 기준 시간 설정
    base_time = None
    for t in reversed(sorted(base_times)):
        if t <= current_hour:
            base_time = t
            break
    
    if base_time is None:
        yesterday = now - timedelta(days=1)
        base_date = yesterday.strftime("%Y%m%d")
        base_time = 23
    
    base_time = f"{base_time:02d}00"
    
    # API 요청
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_SHORT_URL}"
    params = {
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    
    response = await make_request(url=url, params=params)
    data = response.json()
    
    # 응답 처리
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    
    # 시간대별로 데이터 그룹화
    forecasts_by_time = {}
    for item in items:
        fcst_date = item.get("fcstDate")
        fcst_time = item.get("fcstTime")
        key = f"{fcst_date}-{fcst_time}"
        
        if key not in forecasts_by_time:
            forecasts_by_time[key] = {
                "base_date": fcst_date,
                "base_time": fcst_time
            }
        
        # 값 처리
        category = item.get("category")
        value = item.get("fcstValue")
        # 각 카테고리 처리
        if category == "TMP":  # 기온
            forecasts_by_time[key]["temperature"] = float(value)
        elif category == "POP":  # 강수확률
            forecasts_by_time[key]["precipitation_probability"] = int(value)
        elif category == "PTY":  # 강수형태
            forecasts_by_time[key]["precipitation_type"] = int(value)
        elif category == "SKY":  # 하늘상태
            forecasts_by_time[key]["sky_condition"] = int(value)
    
    return list(forecasts_by_time.values())

# 중기예보
async def get_mid_range_forecast(nx: int, ny: int) -> List[Dict[str, Any]]:
    """중기예보 API로 3~7일 후 예보 조회 """
    # 현재 시간
    now = datetime.now()
    today = now.strftime("%Y%m%d")
    current_hour = now.hour
    
    # 중기예보 발표 시간에 따라 4일 또는 5일부터 제공
    # 06시 발표: 4~10일 예보, 18시 발표: 5~10일 예보
    if current_hour < 6:
        # 전날 18시 발표 예보 (5일부터)
        yesterday = now - timedelta(days=1)
        base_date = yesterday.strftime("%Y%m%d")
        base_time = "1800"
        mid_start_day = 5
    elif current_hour < 18:
        # 당일 06시 발표 예보 (4일부터)
        base_date = today
        base_time = "0600"
        mid_start_day = 4
    else:
        # 당일 18시 발표 예보 (5일부터)
        base_date = today
        base_time = "1800"
        mid_start_day = 5
    
    # 위경도를 행정구역코드로 변환
    region_id = convert_grid_to_region(nx, ny)
    
    # 두 API 동시 요청 준비
    temp_url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_MID_OUTLOOK_URL}" # 기온예보
    weather_url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_MID_LAND_URL}" # 육상예보
    
    common_params = {
        "numOfRows": 10,
        "pageNo": 1,
        "dataType": "JSON",
        "regId": region_id,
        "tmFc": f"{base_date}{base_time}"
    }
    
    # 두 API 동시 요청
    temp_response = await make_request(url=temp_url, params=common_params)
    weather_response = await make_request(url=weather_url, params=common_params)
    
    temp_data = temp_response.json()
    weather_data = weather_response.json()
    
    # 데이터 추출
    temp_items = temp_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    weather_items = weather_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    
    if not temp_items or not weather_items:
        return []
    
    # 첫 번째 아이템만 사용
    temp_item = temp_items[0]
    weather_item = weather_items[0]
    
    # 일주일 예보 생성
    forecasts = []
    start_date = now.date()
    
    # 3일 후부터 7일 후까지 데이터 처리
    for i in range(mid_start_day, 11):
        forecast_date = start_date + timedelta(days=i-2)  # 실제 날짜로 변환 (3일 후부터)
        date_str = forecast_date.strftime("%Y%m%d")

        # 중기예보 데이터 키 (i는 원래 키 값 그대로 사용)
        min_key = f"taMin{i}"
        max_key = f"taMax{i}"
        
        # 하늘상태 키
        if i <= 7:  # 7일차까지는 오전/오후 구분
            sky_key = f"wf{i}Pm"  # 오후 데이터 우선
        else:
            sky_key = f"wf{i}"     # 구분 없는 데이터
        
        # 키 존재여부 확인
        if min_key not in temp_item or max_key not in temp_item or sky_key not in weather_item:
            continue
        
        weather_info = convert_weather_condition(weather_item.get(sky_key))
        
        day_forecast = {
            "base_date": date_str,
            "min_temperature": float(temp_item.get(min_key, 0)),
            "max_temperature": float(temp_item.get(max_key, 0)),
            "sky_condition": weather_info["sky_condition"],
            "precipitation_type": weather_info["precipitation_type"],
        }
        
        forecasts.append(day_forecast)
    
    return forecasts

async def get_weather_uvindex(lat: float, lon: float) -> int:
    """
    자외선 지수 조회
    :param lat: 위도
    :param lon: 경도
    :return: 자외선 지수 데이터
    """
    now = datetime.now()
    current_hour = now.hour
    current_datetime = now.strftime("%Y%m%d%H")
    region_data = convert_lat_lon_for_region(lat, lon)
    region_code = region_data.get("region_code")
    
    params = {
        "pageNo": 1,
        "numOfRows": 10,
        "dataType": "JSON",
        "areaNo": region_code,
        "time": current_datetime,
    }
    
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_LIVING_UV_URL}"

    try:
        response = await make_request(url=url, params=params)
        data = response.json()

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            logger.error("자외선 지수 정보를 찾을 수 없습니다.")
            raise HTTPException(status_code=500, detail="자외선 지수 정보를 찾을 수 없습니다.")
        
        uv_data = items[0]
            
        best_uv_index = "0"
        min_hour_diff = float('inf')

        for hour_offset in range(0, 25, 3):
            key = f"h{hour_offset}"
            if key in uv_data:
                uv_value = uv_data[key]

                if uv_value == "" or uv_value is None:
                    continue
                
                hour_diff = abs(current_hour - hour_offset)
        
                if hour_diff > 12:
                    hour_diff = 24 - hour_diff
                
                if hour_diff < min_hour_diff:
                    min_hour_diff = hour_diff
                    best_uv_index = uv_value
        try:
            return int(float(best_uv_index)) if best_uv_index and best_uv_index.strip() != "" else 0
        except (ValueError, AttributeError):
            return 0
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자외선 지수 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자외선 지수 조회 오류: {str(e)}")