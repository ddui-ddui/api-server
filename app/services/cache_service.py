import json
from typing import Optional
from datetime import datetime
from app.config.redis_config import RedisClient
from app.models.air_quality import HourlyAirQualityCache, WeeklyAirQualityCache
import logging

logger = logging.getLogger()

class AirQualityCacheService:
    def __init__(self):
        self.redis_client = RedisClient()
        self.HOURLY_KEY = "air_quality:hourly"
        self.WEEKLY_KEY = "air_quality:weekly"

        # 시간별 캐시 관리
    async def get_hourly_cache(self) -> Optional[HourlyAirQualityCache]:
        """시간별 대기질 캐시 조회"""
        try:
            redis = await self.redis_client.get_client()
            cached_data = await redis.get(self.HOURLY_KEY)
            
            if cached_data:
                data_dict = json.loads(cached_data)
                return HourlyAirQualityCache(**data_dict)
        except Exception as e:
            logger.error(f"시간별 캐시 조회 실패: {str(e)}")
        return None
    
    async def set_hourly_cache(self, cache_data: HourlyAirQualityCache):
        """시간별 대기질 캐시 저장"""
        try:
            redis = await self.redis_client.get_client()
            
            data_dict = cache_data.model_dump()            
            await redis.set(self.HOURLY_KEY, json.dumps(data_dict))
            logger.info(f"시간별 캐시 저장 완료")
        except Exception as e:
            logger.error(f"시간별 캐시 저장 실패: {str(e)}")

    async def get_weekly_cache(self) -> Optional[WeeklyAirQualityCache]:
        """주간별 대기질 캐시 조회"""
        try:
            redis = await self.redis_client.get_client()
            cached_data = await redis.get(self.WEEKLY_KEY)
            
            if cached_data:
                data_dict = json.loads(cached_data)
                return WeeklyAirQualityCache(**data_dict)
        except Exception as e:
            logger.error(f"주간별 캐시 조회 실패: {str(e)}")
        return None
    
    async def set_weekly_cache(self, cache_data: WeeklyAirQualityCache):
        """주간별 대기질 캐시 저장"""
        try:
            redis = await self.redis_client.get_client()
            
            data_dict = cache_data.model_dump()
            await redis.set(self.WEEKLY_KEY, json.dumps(data_dict))
            logger.info(f"주간별 캐시 저장 완료")
        except Exception as e:
            logger.error(f"주간별 캐시 저장 실패: {str(e)}")

redis_service = AirQualityCacheService()