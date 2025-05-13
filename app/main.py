from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router

app = FastAPI(
    title="DDUI DDUI API Server",
    description="날씨 정보와 미세먼지 데이터를 기반으로 산책 적합도를 제공하는 API",
    version="0.1.0",
    openapi_tags=[
        {
            "name": "weather",
            "description": "날씨 정보 관련 API",
        },
        {
            "name": "dust",
            "description": "미세먼지 정보 관련 API",
        },
        {
            "name": "walkability",
            "description": "산책 적합도 관련 API",
        },
    ],
)

app.include_router(api_router, prefix=settings.API_V1_URL)