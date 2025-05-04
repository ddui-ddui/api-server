import httpx
import certifi
from app.core.config import settings
from typing import Dict, Any, Optional

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

async def make_request(
    url: str, 
    method: str = "GET", 
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None
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
        
    Returns:
        httpx.Response: HTTP 응답 객체
    """
    async with await get_http_client() as client:
        if method.upper() == "GET":
            response = await client.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, params=params, data=data, json=json_data, headers=headers)
        elif method.upper() == "PUT":
            response = await client.put(url, params=params, data=data, json=json_data, headers=headers)
        elif method.upper() == "DELETE":
            response = await client.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        return response