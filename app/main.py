from fastapi import FastAPI, Request
from app.core.config import settings
from app.api.api import api_router
from fastapi.middleware.cors import CORSMiddleware
from app.config.logging_config import get_logger
from app.config.context import request_id, client_ip, user_agent
# import logging
import time
import uuid

logger = get_logger()

# log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
# if settings.ENVIRONMENT == "production":
#     logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
#     logging.getLogger("uvicorn").setLevel(logging.INFO)
# else:
#     logging.getLogger("uvicorn.access").setLevel(log_level)
#     logging.getLogger("uvicorn").setLevel(log_level)


app = FastAPI(
    title="DDUI DDUI API Server",
    description="날씨 정보와 미세먼지 데이터를 기반으로 산책 적합도를 제공하는 API",
    version="0.1.0",
    openapi_tags=[
        # {
        #     "name": "weather",
        #     "description": "산책 적합도 관련 API",
        # },
        {
            "name": "walkability",
            "description": "산책 적합도 관련 API",
        }
    ],
)

logger.info("DDUI DDUI API Server starting...")

# CORS 설정
if settings.ENVIRONMENT == "production":
    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
            "https://dduiddui.kr",
            "https://www.dduiddui.kr",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    req_id_value = str(uuid.uuid4())[:8]
    
    # 클라이언트 IP 가져오기 (프록시 고려)
    client_ip_value = request.headers.get("x-forwarded-for")
    if client_ip_value:
        client_ip_value = client_ip_value.split(",")[0].strip()
    else:
        client_ip_value = request.client.host if request.client else "unknown"
    
    # User Agent 가져오기
    user_agent_value = request.headers.get("user-agent", "unknown")

    # 컨텍스트 변수 설정
    request_id.set(req_id_value)
    client_ip.set(client_ip_value)
    user_agent.set(user_agent_value)
    
    try:
        # 요청 로깅
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # 응답 시간 로깅
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
        
        return response
        
    except Exception as e:
        # 에러 발생 시에도 로깅
        process_time = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)} - {process_time:.4f}s")
        raise
    
app.include_router(api_router, prefix=settings.API_V1_URL)