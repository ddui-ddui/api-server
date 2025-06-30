from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.common.cache_on_startup import initialize_hourly_cache, initialize_weekly_cache
import logging

logger = logging.getLogger()

class AirQualityScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def setup_jobs(self):
        """스케줄 작업 설정"""
        # 시간별 캐시 갱신: 5:30, 11:30, 17:30, 23:30
        self.scheduler.add_job(
            func=self._update_hourly_cache,
            trigger=CronTrigger(hour="5,11,17,23", minute=30),
            id="hourly_cache_update",
            name="시간별 대기질 캐시 갱신"
        )
        
        # 주간별 캐시 갱신: 매일 자정
        self.scheduler.add_job(
            func=self._update_weekly_cache,
            trigger=CronTrigger(hour=0, minute=0),
            id="weekly_cache_update", 
            name="주간별 대기질 캐시 갱신"
        )
    
    async def _update_hourly_cache(self):
        """시간별 캐시 갱신 작업"""
        try:
            logger.info("시간별 캐시 갱신 시작")
            await initialize_hourly_cache()
            logger.info("시간별 캐시 갱신 완료")
        except Exception as e:
            logger.error(f"시간별 캐시 갱신 실패: {str(e)}")
    
    async def _update_weekly_cache(self):
        """주간별 캐시 갱신 작업"""
        try:
            logger.info("주간별 캐시 갱신 시작")
            await initialize_weekly_cache()
            logger.info("주간별 캐시 갱신 완료")
        except Exception as e:
            logger.error(f"주간별 캐시 갱신 실패: {str(e)}")
    
    def start(self):
        """스케줄러 시작"""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("대기질 캐시 스케줄러 시작됨")
    
    def shutdown(self):
        """스케줄러 종료"""
        self.scheduler.shutdown()
        logger.info("대기질 캐시 스케줄러 종료됨")

# 전역 스케줄러 인스턴스
air_quality_scheduler = AirQualityScheduler()