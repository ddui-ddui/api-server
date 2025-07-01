from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.common.cache_on_startup import initialize_hourly_cache, initialize_weekly_cache
from app.config.logging_config import get_logger

class AirQualityScheduler:
    def __init__(self):
        self.logger = get_logger()
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                'coalesce': True,  # 중복된 작업을 하나로 합침
                'max_instances': 1,  # 동시에 실행되는 작업의 최대 인스턴스 수
                'misfire_grace_time': 60 * 5,  # 작업이 지연될 경우 최대 5분까지 기다림
            }
        )
    
    def _setup_jobs(self):
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
            self.logger.info("시간별 캐시 갱신 시작")
            await initialize_hourly_cache()
            self.logger.info("시간별 캐시 갱신 완료")
        except Exception as e:
            self.logger.error(f"시간별 캐시 갱신 실패: {str(e)}")
    
    async def _update_weekly_cache(self):
        """주간별 캐시 갱신 작업"""
        try:
            self.logger.info("주간별 캐시 갱신 시작")
            await initialize_weekly_cache()
            self.logger.info("주간별 캐시 갱신 완료")
        except Exception as e:
            self.logger.error(f"주간별 캐시 갱신 실패: {str(e)}")
    
    def start(self):
        """스케줄러 시작"""
        if self.scheduler.running:
            self.logger.warning("스케줄러가 이미 실행 중입니다.")
            return
            
        self.logger.info("start() 메서드 호출됨!")
        try:
            self._setup_jobs()
            self.logger.info("스케줄러 시작 중...")
            self.scheduler.start()
            self.logger.info("대기질 캐시 스케줄러 시작됨")
            
            # 등록된 작업 목록 출력
            jobs = self.scheduler.get_jobs()
            self.logger.info(f"등록된 작업 수: {len(jobs)}")
            for job in jobs:
                self.logger.info(f"- {job.name} (ID: {job.id})")
                
        except Exception as e:
            self.logger.error(f"스케줄러 시작 중 오류: {str(e)}")
            import traceback
            self.logger.error(f"상세 에러: {traceback.format_exc()}")
            raise
    
    def shutdown(self):
        """스케줄러 종료"""
        try:
            if hasattr(self.scheduler, 'shutdown'):
                self.scheduler.shutdown()
                self.logger.info("대기질 캐시 스케줄러 종료됨")
        except Exception as e:
            self.logger.error(f"스케줄러 종료 중 오류: {str(e)}")

# 전역 스케줄러 인스턴스
air_quality_scheduler = AirQualityScheduler()