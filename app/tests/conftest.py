import asyncio
from anyio import Path
from fastapi.testclient import TestClient
import pytest
import os
from unittest.mock import MagicMock, patch
from loguru import logger
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 테스트 환경 설정
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "DEBUG"

@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """테스트용 로깅 설정"""
    # 기존 로거 핸들러 제거
    logger.remove()
    
    # 테스트용 간단한 로깅 설정
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <3}</level> | <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )
    
    return logger

@pytest.fixture(autouse=True)
def mock_context_vars():
    """테스트에서 컨텍스트 변수 모킹"""
    mock_request_id = MagicMock()
    mock_request_id.get.return_value = "test-req-123"
    
    mock_client_ip = MagicMock()
    mock_client_ip.get.return_value = "127.0.0.1"
    
    mock_user_agent = MagicMock()
    mock_user_agent.get.return_value = "test-agent"
    
    with patch('app.config.context.request_id', mock_request_id), \
         patch('app.config.context.client_ip', mock_client_ip), \
         patch('app.config.context.user_agent', mock_user_agent):
        yield

@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 설정"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def app():
    """테스트용 FastAPI 앱 (lifespan 없이)"""
    # 테스트 전용 환경변수 설정
    os.environ["REDIS_URL"] = "redis://fake-redis:6379"
    
    # Redis와 스케줄러 모킹
    with patch('app.config.redis_config.redis_client') as mock_redis, \
         patch('app.core.air_quality_schedule.air_quality_scheduler') as mock_scheduler, \
         patch('app.common.cache_on_startup.initialize_cache_on_startup') as mock_cache:
        
        mock_redis.close = MagicMock()
        mock_scheduler.start = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        mock_cache.return_value = None
        
        # 테스트용 간단한 앱 생성 (lifespan 없이)
        from fastapi import FastAPI
        from app.api.api import api_router
        from app.api.endpoints.walkability import router as walkability_router
        from fastapi.middleware.cors import CORSMiddleware
        
        test_app = FastAPI(
            title="Test DDUI DDUI API Server",
            description="테스트용 API",
            version="0.1.0",
            docs_url="/docs"
        )
        
        # API 라우터 포함
        test_app.include_router(walkability_router, prefix="/api/v1/walkability", tags=["walkability"])
        
        # CORS 설정
        test_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        yield test_app

@pytest.fixture(scope="session")
def client(app):
    """테스트 클라이언트"""
    with TestClient(app) as test_client:
        yield test_client

# C 클래스란?
# 파이썬의 C API를 통해 구현된 클래스를 말한다.
# 그래서 런타임 후에 속성이나 메서드를 추가하거나 변경할 수 없다.

# patch의 의미는
# 원본 객체를 대체하여 테스트 환경에서 가짜 객체로 교체하는 것.

# ContextVar?
# 비동기 환경에서 컨텍스트별 변수를 관리하는 클래스이다.
# 전역 변수와 유사하지만, 비동기 코드에서 각 작업의 컨텍스트를 분리하여 관리할 수 있다.
# 예를 들어, 웹 요청의 ID나 사용자 정보를 각 요청별로 저장하고 싶을 때 유용하다.
# 나 같은 경우는 한 요청에 대한 IP, User-Agent, Request ID 등을 로깅을 위헤 사용했다.