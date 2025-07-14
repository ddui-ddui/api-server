import asyncio
from datetime import datetime
from app.models.air_quality import HourlyAirQualityCache, WeeklyAirQualityCache
from app.services.air_quality import fetch_hourly_air_quality_raw, process_weekly_air_quality_for_cache
from app.services.cache_service import AirQualityCacheService, air_quality_cache_service
import logging

logger = logging.getLogger()

async def initialize_cache_on_startup():
    """서버 시작 시 캐시 초기화"""
    try:
        logger.info("캐시 초기화 시작")
        
        # 1. 시간별 캐시 확인
        hourly_cache = await air_quality_cache_service.get_hourly_cache()
        if hourly_cache is None:
            logger.info("시간별 캐시 없음 - 초기 데이터 로드 필요")
            await initialize_hourly_cache()
        else:
            logger.info("시간별 캐시 존재")
        
        # 2. 주간별 캐시 확인  
        weekly_cache = await air_quality_cache_service.get_weekly_cache()
        if weekly_cache is None:
            logger.info("주간별 캐시 없음 - 초기 데이터 로드 필요")
            await initialize_weekly_cache()
        else:
            logger.info("주간별 캐시 존재")
            
        logger.info("캐시 초기화 완료")
    except Exception as e:
        logger.error(f"캐시 초기화 실패: {str(e)}")

async def initialize_hourly_cache():
    """시간별 캐시 초기 로드"""

    # 최대 재시도 횟수 10회
    # 재시도 간격 5분
    # 호출 안되는 시간이 존재함
    max_attempts = 10
    retry_delay = 300  # 5분 간격

    for attempt in range(max_attempts + 1):
        try:
            logger.info(f"시간별 캐시 초기화 시도 {attempt}/{max_attempts}")

            now = datetime.now()
            search_date = now.strftime("%Y-%m-%d")
            
            # API에서 원본 데이터 조회
            raw_data = await fetch_hourly_air_quality_raw(search_date)
            print(f"원본 데이터 로드 완료")
            
            # 원본 데이터를 캐시에 저장
            cache_data = HourlyAirQualityCache(
                forecasts=raw_data,  # 원본 API 데이터 저장
                cached_at=datetime.now().isoformat()
            )
            
            await AirQualityCacheService().set_hourly_cache(cache_data)
            logger.info("시간별 캐시 초기 로드 완료")
            return
        except Exception as e:
            logger.error(f"시간별 캐시 초기 로드 실패: {str(e)}")
            if attempt == max_attempts:
                logger.error("최대 재시도 횟수 초과 - 시간별 캐시 초기화 실패")
                raise Exception(f"시간별 캐시 초기화 실패")
            
            logger.info(f"{retry_delay}초 후 재시도...")
            await asyncio.sleep(retry_delay)

async def initialize_weekly_cache():
    """주간별 캐시 초기 로드"""

    # 최대 재시도 횟수 10회
    # 재시도 간격 5분
    # 호출 안되는 시간이 존재함
    max_attempts = 10
    retry_delay = 300  # 5분 간격
    for attempt in range(max_attempts + 1):
        try:
            logger.info(f"주간별 캐시 초기화 시도 {attempt}/{max_attempts}")
            
            # process_weekly_air_quality_for_cache() 호출해서 가공된 데이터 생성
            processed_forecasts = await process_weekly_air_quality_for_cache()
            logger.info(f"원본 데이터 로드 완료: {len(processed_forecasts)}개 항목")
            
            # 캐시에 저장
            cache_data = WeeklyAirQualityCache(
                forecasts=processed_forecasts,
                cached_at=datetime.now().isoformat()
            )
            
            await AirQualityCacheService().set_weekly_cache(cache_data)
            logger.info(f"주간별 대기질 데이터 캐시 로드 완료")
            return
        except Exception as e:
            logger.error(f"주간별 캐시 초기 로드 실패: {str(e)}")
            if attempt == max_attempts:
                logger.error("최대 재시도 횟수 초과 - 주간별 캐시 초기화 실패")
                raise Exception(f"주간별 캐시 초기화 실패")
            
            logger.info(f"{retry_delay}초 후 재시도...")
            await asyncio.sleep(retry_delay)