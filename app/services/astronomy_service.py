from urllib.parse import unquote
from fastapi import HTTPException
import httpx
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from app.common.http_client import make_request
from app.core.config import settings
from app.config.logging_config import get_logger
logger = get_logger()


async def get_sunrise_sunset(lat: float, lon: float, retry_days:int = 0) -> dict[str, str]:
    """
    주어진 위도와 경도로 일출 및 일몰 시간 조회
    :param lat: 위도
    :param lon: 경도
    :return: 일출 및 일몰 시간 정보
    """

    # 날짜 셋팅
    MAX_RETRY_DAYS = 7
    if retry_days > MAX_RETRY_DAYS:
        raise HTTPException(status_code=400, detail=f"일출/일몰 시간을 조회할 수 없습니다.")
    
    target_date = datetime.now() - timedelta(days=retry_days)
    date_str = target_date.strftime("%Y%m%d")
    logger.info(f"일출/일몰 조회 시도: {date_str} (retry_days: {retry_days})")

    # Request URL
    params = {
        "locdate"	: date_str,
        "longitude": lon,	
        "latitude"	: lat,
        "dnYn" : "Y"
    }
    url = f"{settings.GOV_DATA_BASE_URL}{settings.GOV_DATA_ASTRONOMY_SUN_URL}"

    try:
        response = await make_request(url=url, params=params)
        root = ET.fromstring(response.text)
        
        # xml에서 일출 및 일몰 시간 추출
        item = root.find('.//item')
        if item is None:
            logger.warning(f"일출/일몰 데이터 없음 (retry_days: {retry_days})")
            if retry_days < MAX_RETRY_DAYS:
                return await get_sunrise_sunset(lat, lon, retry_days + 1)
            raise HTTPException(status_code=404, detail="일출/일몰 데이터를 찾을 수 없습니다.")
            
        
        sunrise_elem = item.find('sunrise')
        sunset_elem = item.find('sunset')

        if sunrise_elem is None or sunset_elem is None:
            logger.warning(f"일출/일몰 시간 정보 없음 (retry_days: {retry_days})")
            if retry_days < MAX_RETRY_DAYS:
                return await get_sunrise_sunset(lat, lon, retry_days + 1)
            raise HTTPException(status_code=404, detail="일출/일몰 시간 정보를 찾을 수 없습니다.")

        # 시간 형식 변환
        try:
            # xml에서 텍스트 추출
            sunrise = sunrise_elem.text.strip()
            sunset = sunset_elem.text.strip()
            sunrise_time = f"{sunrise[:2]}:{sunrise[2:]}"
            sunset_time = f"{sunset[:2]}:{sunset[2:]}"
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"시간 형식 변환 오류: {str(e)}")\
        
        # 결과 데이터 추출        
        return {
            "sunrise": sunrise_time,
            "sunset": sunset_time,
        }
    except HTTPException:
        raise
    except ET.ParseError as e:
        logger.error(f"XML 파싱 오류: {str(e)}")
        if retry_days < MAX_RETRY_DAYS:
            return await get_sunrise_sunset(lat, lon, retry_days + 1)
        raise HTTPException(status_code=500, detail="XML 응답 형식 오류")
    except Exception as e:
        logger.error(f"한국천문연구원 데이터 처리 오류: {str(e)}")
        if retry_days < MAX_RETRY_DAYS:
            logger.info(f"일출/일몰 조회 재시도: {retry_days + 1}일 전")
            return await get_sunrise_sunset(lat, lon, retry_days + 1)
        raise HTTPException(status_code=500, detail="천문 서비스 오류")