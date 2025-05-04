import httpx
from fastapi import HTTPException
from app.core.config import settings
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from app.utils.convert_for_grid import mapToGrid
from app.common.http_client import make_request
from urllib.parse import unquote



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
            print(data)

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
                "wind_speed": float(weather_data.get("WSD", 0)), 
                "wind_direction": int(weather_data.get("VEC", 0)),
                "forecast_time": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]} {closest_time[:2]}:{closest_time[2:]}",  # 예보 시간
                "base_time": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]} {base_time[:2]}:{base_time[2:]}",  # 발표 기준 시간
            }
            return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"기상청 API 오류: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"기상청 API 서비스에 연결할 수 없습니다: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"날씨 데이터 처리 오류: {str(e)}")
                    



    