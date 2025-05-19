from typing import Any, Dict, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

def success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    """
    성공 응답을 위한 공통 형식
    
    Args:
        data: 응답 데이터
        message: 성공 메시지
    
    Returns:
        dict: 성공 응답 형식
    """
    response = {
        "status": 200,
        "message": message
    }
    if data is not None:
        response["data"] = data
    
    return response

def error_response(status_code: int, error_message: str) -> HTTPException:
    """
    에러 응답을 위한 공통 형식을 생성하는 함수
    
    Args:
        status_code: HTTP 상태 코드
        error_message: 에러 메시지
    
    Returns:
        HTTPException: FastAPI에서 처리할 수 있는 예외 객체
    """
    detail = {
        "status": status_code,
        "message": "failure",
    }
    
    if error_message:
        detail["error"] = error_message
    
    return HTTPException(
        status_code=status_code,
        detail=detail
    )