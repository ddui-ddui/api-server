from fastapi import FastAPI, Request
from app.core.config import settings
from app.api.api import api_router
from fastapi.middleware.cors import CORSMiddleware
from app.config.logging_config import setup_logging, get_logger
import logging
import time

setup_logging()
logger = get_logger()

log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
if settings.ENVIRONMENT == "production":
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
else:
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("uvicorn").setLevel(log_level)


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
    
    # 클라이언트 IP 가져오기 (프록시 고려)
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # User Agent 가져오기
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 요청 로깅
    logger.info(f"Request: {client_ip} - {request.method} {request.url.path} - User-Agent: {user_agent}")
    
    response = await call_next(request)
    
    # 응답 시간 로깅
    process_time = time.time() - start_time
    logger.info(f"Response: {client_ip} - {response.status_code} - {process_time:.4f}s")
    
    return response

app.include_router(api_router, prefix=settings.API_V1_URL)