import json
from fastapi import HTTPException
import httpx
import certifi
from app.core.config import settings
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
from app.config.logging_config import get_logger
logger = get_logger()

async def get_http_client() -> httpx.AsyncClient:
    """
    SSL 설정이 적용된 httpx AsyncClient를 반환합니다.
    
    Returns:
        httpx.AsyncClient: 구성된 HTTP 클라이언트
    """
    # SSL 설정 적용
    ssl_verify = certifi.where() if settings.SSL_VERIFY else False
    
    # 타임아웃 설정 추가
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    return httpx.AsyncClient(
        verify=ssl_verify,
        timeout=timeout
    )

def handle_response_error(response_code: str, response_msg: str) -> None:
    logger.error(f"API 오류 (Code: {response_code}): {response_msg}")
    if response_code == "01":  # APPLICATION_ERROR
        raise HTTPException(status_code=500, detail=f"어플리케이션 에러: {response_msg}")
    elif response_code == "02":  # DB_ERROR
        raise HTTPException(status_code=500, detail=f"데이터베이스 에러: {response_msg}")
    elif response_code == "03":  # NODATA_ERROR
        raise HTTPException(status_code=404, detail=f"데이터없음: {response_msg}")
    elif response_code == "04":  # HTTP_ERROR
        raise HTTPException(status_code=500, detail=f"HTTP 에러: {response_msg}")
    elif response_code == "05":  # SERVICETIME_OUT
        raise HTTPException(status_code=503, detail=f"서비스 연결실패: {response_msg}")
    elif response_code == "10":  # INVALID_REQUEST_PARAMETER_ERROR
        raise HTTPException(status_code=400, detail=f"잘못된 요청 파라메터: {response_msg}")
    elif response_code == "11":  # NO_MANDATORY_REQUEST_PARAMETERS_ERROR
        raise HTTPException(status_code=400, detail=f"필수요청 파라메터 없음: {response_msg}")
    elif response_code == "12":  # NO_OPENAPI_SERVICE_ERROR
        raise HTTPException(status_code=404, detail=f"해당 오픈API서비스 없음: {response_msg}")
    elif response_code == "20":  # SERVICE_ACCESS_DENIED_ERROR
        raise HTTPException(status_code=403, detail=f"서비스 접근거부: {response_msg}")
    elif response_code == "21":  # TEMPORARILY_DISABLE_THE_SERVICEKEY_ERROR
        raise HTTPException(status_code=503, detail=f"일시적으로 사용불가 서비스키: {response_msg}")
    elif response_code == "22":  # LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR
        raise HTTPException(status_code=429, detail=f"서비스 요청제한횟수 초과: {response_msg}")
    elif response_code == "30":  # SERVICE_KEY_IS_NOT_REGISTERED_ERROR
        raise HTTPException(status_code=401, detail=f"등록되지 않은 서비스키: {response_msg}")
    elif response_code == "31":  # DEADLINE_HAS_EXPIRED_ERROR
        raise HTTPException(status_code=401, detail=f"기한만료 서비스키: {response_msg}")
    elif response_code == "32":  # UNREGISTERED_IP_ERROR
        raise HTTPException(status_code=403, detail=f"등록되지 않은 IP: {response_msg}")
    elif response_code == "33":  # UNSIGNED_CALL_ERROR
        raise HTTPException(status_code=401, detail=f"서명되지 않은 호출: {response_msg}")
    elif response_code == "99":  # UNKNOWN_ERROR
        raise HTTPException(status_code=500, detail=f"기타에러: {response_msg}")
    else:
        # 예상하지 못한 에러 코드
        raise HTTPException(status_code=500, detail=f"알 수 없는 에러 코드({response_code}): {response_msg}")

async def make_request(
    url: str, 
    method: str = "GET", 
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    response_format: str = "json"
) -> httpx.Response:
    """
    HTTP 요청을 보내는 공통 함수
    
    Args:
        url: 요청 URL
        method: HTTP 메서드 (GET, POST 등)
        params: URL 쿼리 파라미터
        data: 요청 body (form data)
        headers: HTTP 헤더
        json_data: JSON 데이터 (application/json)
        response_format: 응답 형식 (json, xml)
    Returns:
        httpx.Response: HTTP 응답 객체
    """
    logger.info(f"Request Url: {url}")
    logger.info(f"param: {params}")
    async with await get_http_client() as client:
        if method.upper() == "GET":
            response = await client.get(url, params=params, headers=headers)
        # elif method.upper() == "POST":
        #     response = await client.post(url, params=params, data=data, json=json_data, headers=headers)
        # elif method.upper() == "PUT":
        #     response = await client.put(url, params=params, data=data, json=json_data, headers=headers)
        # elif method.upper() == "DELETE":
        #     response = await client.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        logger.info(f"Low Json Data: {response.text}")
        if response_format.lower() == "json":
            try:
                data = response.json()
                response_code = data.get("response", {}).get("header", {}).get("resultCode")
                response_msg = data.get("response", {}).get("header", {}).get("resultMsg", "Unknown error")
                logger.info(f"Response Code: {response_code}, Message: {response_msg}")
                if response_code != "00":
                    handle_response_error(response_code, response_msg)
                        
            except json.JSONDecodeError:
                logger.error("JSON 응답 파싱 오류")
                raise HTTPException(status_code=500, detail="API 응답 형식 오류")
                
        elif response_format.lower() == "xml":
            try:
                root = ET.fromstring(response.text)
               
                result_code = root.find('.//resultCode')
                result_msg = root.find('.//resultMsg')

                response_code = result_code.text if result_code is not None else "Unknown"
                response_msg = result_msg.text if result_msg is not None else "Unknown error"
                logger.info(f"Response Code: {response_code}, Message: {response_msg}")
                if response_code != "00":
                    handle_response_error(response_code, response_msg)
                    
            except ET.ParseError:
                logger.error("XML 응답 파싱 오류")
                raise HTTPException(status_code=500, detail="XML 응답 형식 오류")

        return response