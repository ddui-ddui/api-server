import redis.asyncio as redis
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger()

class RedisClient:
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_client(self) -> redis.Redis:
        if self._client is None:
            try:
                host = settings.REDIS_HOST
                port = settings.REDIS_PORT
                db = settings.REDIS_DB

                self._client = redis.Redis(
                    host=host,
                    port=port,
                    password=settings.REDIS_PASSWORD,
                    db=db,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    encoding='utf-8',
                )
                
                # 연결 테스트
                await self._client.ping()
                logger.info(f"Redis 연결 성공: {host}:{port} (DB: {db})")
                
            except Exception as e:
                logger.error(f"Redis 연결 실패: {str(e)}")
                self._client = None
                raise
                
        return self._client
    
    async def close(self):
        """Redis 연결 종료"""
        if self._client:
            await self._client.close()
            self._client = None

# 전역 Redis 클라이언트
redis_client = RedisClient()

async def get_redis() -> redis.Redis:
    return await redis_client.get_client()