from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(api_router, prefix=settings.API_V1_URL)