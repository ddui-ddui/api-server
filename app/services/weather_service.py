import httpx
from fastapi import HTTPException
from app.core.config import settings
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from app.utils.convert_for_grid import mapToGrid
from app.common.http_client import make_request
from urllib.parse import unquote
from app.utils.weather_format_utils import get_wind_direction, convert_wind_speed



async def get_ultra_short_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """
    초단기 예보 조회
    :param nx: 예보지점 X 좌표
    :param ny: 예보지점 Y 좌표
    :return: 초단기 예보 데이터
    """

    # Coordinates for Seoul
    # nx, ny = mapToGrid(lat, lon)

    nx = 60
    ny = 127

    
    # Current time
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")

    if now.minute < 45:
        now = now - timedelta(hours=1)
    base_time =now.strftime("%H00")
    current_fcst_time = now.strftime("%H%M")


    # Request URL
    params = {
        "serviceKey": unquote(settings.GOV_DATA_API_KEY),
        "numOfRows": 1000,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    print(params)
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_WEATHER_ULTRA_SHORT_URL}"

    try:
            response = await make_request(url=url, params=params)
            response.raise_for_status()
            data = response.json()

            # 응답 코드 확인
            response_code = data.get("response", {}).get("header", {}).get("resultCode")
            if response_code != "00":
                response_msg = data.get("response", {}).get("header", {}).get("resultMsg", "Unknown error")
                raise HTTPException(status_code=500, detail=f"기상청 API 오류: {response_msg}")
            
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
            
            def convert_rainfall(value):
                if value in ["강수없음", "없음"]:
                    return 0.0
                try:
                    return float(value)
                except:
                    return 0.0

            result = {
                "temperature": float(weather_data.get("T1H", 0)),
                "rainfall": convert_rainfall(weather_data.get("RN1", 0)), 
                "sky_condition": int(weather_data.get("SKY", 0)),
                "humidity": int(weather_data.get("REH", 0)),
                "precipitation_type": int(weather_data.get("PTY", 0)),
                "wind_speed": convert_wind_speed(weather_data.get("WSD", 0), "m/s"), 
                "wind_direction": get_wind_direction(int(weather_data.get("VEC", 0))),
                "forecast_time": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]} {closest_time[:2]}:{closest_time[2:]}",
                "base_time": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]} {base_time[:2]}:{base_time[2:]}",
            }
            return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"기상청 API 오류: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"기상청 API 서비스에 연결할 수 없습니다: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"날씨 데이터 처리 오류: {str(e)}")

async def get_hourly_forecast(lat: float, lon: float, hours: int = 12) -> Dict[str, Any]:
    """
    시간별 예보 조회 (최대 67시간)
    :param lat: 위도
    :param lon: 경도
    :param hours: 조회할 시간 수 (기본값: 12시간)
    :return: 시간별 예보 데이터 리스트
    """
    # 좌표 변환 (실제 변환 필요 시 주석 해제)
    # nx, ny = mapToGrid(lat, lon)
    
    nx = 60
    ny = 127
    
    # Current time
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    
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
        "serviceKey": unquote(settings.GOV_DATA_API_KEY),
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
        response.raise_for_status()
        data = response.json()
        
        # 응답 코드 확인
        response_code = data.get("response", {}).get("header", {}).get("resultCode")
        if response_code != "00":
            response_msg = data.get("response", {}).get("header", {}).get("resultMsg", "Unknown error")
            raise HTTPException(status_code=500, detail=f"기상청 API 오류: {response_msg}")
        
        # 결과 데이터 추출
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
            
            # 값 추가 (카테고리별로)
            category = item.get("category")
            value = item.get("fcstValue")
            
            # 각 카테고리 처리
            if category == "TMP":  # 기온
                forecasts_by_time[key]["temperature"] = float(value)
            elif category == "POP":  # 강수확률
                forecasts_by_time[key]["precipitation_probability"] = int(value)
            elif category == "PTY":  # 강수형태
                forecasts_by_time[key]["precipitation_type"] = int(value)
            elif category == "PCP":  # 1시간 강수량
                if value == "강수없음":
                    forecasts_by_time[key]["rainfall"] = 0.0
                elif "미만" in value:
                    # "1 미만"과 같은 값을 처리
                    forecasts_by_time[key]["rainfall"] = 0.1  # 또는 다른 적절한 기본값
                else:
                    try:
                        forecasts_by_time[key]["rainfall"] = float(value.replace("mm", ""))
                    except ValueError:
                        # 변환 실패 시 기본값 사용
                        forecasts_by_time[key]["rainfall"] = 0.0
            elif category == "REH":  # 습도
                forecasts_by_time[key]["humidity"] = int(value)
            elif category == "SKY":  # 하늘상태
                forecasts_by_time[key]["sky_condition"] = int(value)
            elif category == "WSD":  # 풍속
                forecasts_by_time[key]["wind_speed"] = float(value)
            elif category == "VEC":  # 풍향
                forecasts_by_time[key]["wind_direction"] = int(value)
            elif category == "TMN":  # 최저기온
                forecasts_by_time[key]["min_temperature"] = float(value)
            elif category == "TMX":  # 최고기온
                forecasts_by_time[key]["max_temperature"] = float(value)
        
        # 현재 시간부터 지정된 시간까지의 예보만 추출
        result_forecasts = []
        
        # 시간 정렬
        sorted_keys = sorted(forecasts_by_time.keys())
        count = 0
        for key in sorted_keys:
            forecast = forecasts_by_time[key]
            # 필수 필드 확인
            required_fields = ["temperature", 
                               "precipitation_probability", 
                               "sky_condition", 
                               "humidity", 
                               "wind_speed", 
                               "wind_direction", 
                               "precipitation_type", 
                               "rainfall"
                               ]
            if all(field in forecast for field in required_fields):
                # 날짜 형식 정리
                fcst_date = forecast["forecast_date"]
                fcst_time = forecast["forecast_time"]
                forecast["forecast_time_formatted"] = f"{fcst_date[:4]}-{fcst_date[4:6]}-{fcst_date[6:]} {fcst_time[:2]}:{fcst_time[2:]}"
                print(forecast["wind_speed"])
                print(forecast["wind_direction"])
                forecast["wind_speed"] = convert_wind_speed(forecast["wind_speed"], "m/s")
                forecast["wind_direction"] = get_wind_direction(forecast["wind_direction"])
                result_forecasts.append(forecast)
                count += 1
                
                # 지정된 시간 수에 도달하면 중단
                if count >= hours:
                    break
        
        # 메타데이터 추가
        result = {
            "base_date": base_date,
            "base_time": base_time,
            "base_time_formatted": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]} {base_time[:2]}:{base_time[2:]}",
            "forecasts": result_forecasts
        }
        
        return result
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"기상청 API 오류: {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"기상청 API 서비스에 연결할 수 없습니다: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"날씨 데이터 처리 오류: {str(e)}")