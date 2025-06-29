import threading
from urllib.parse import unquote
from app.core.config import settings
from app.config.logging_config import get_logger

logger = get_logger()

class ServiceKeyRotator:
    def __init__(self):
        self.service_keys = [
            settings.GOV_DATA_API_KEY_1,
            settings.GOV_DATA_API_KEY_2,
            # settings.SERVICE_KEY_3,  # 나중에 추가 시
        ]
        self.current_index = 0
        self._lock = threading.Lock()
        logger.info(f"서비스 키 로테이터 초기화 완료 - 총 {len(self.service_keys)}개 키")
    
    def get_next_service_key(self) -> str:
        """다음 서비스 키를 반환하고 인덱스를 증가"""
        with self._lock:
            current_key = self.service_keys[self.current_index]
            key_index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.service_keys)
            logger.debug(f"서비스 키 사용: 인덱스 {key_index}")
            return unquote(current_key)
    
    def force_rotate(self):
        """강제로 다음 키로 로테이션 (에러 발생 시 사용)"""
        with self._lock:
            old_index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.service_keys)
            logger.warning(f"서비스 키 강제 로테이션: {old_index} -> {self.current_index}")
    
    
    def get_current_stats(self) -> dict:
        """현재 상태 정보 반환"""
        with self._lock:
            return {
                "total_keys": len(self.service_keys),
                "current_index": self.current_index,
                "next_key_preview": self.service_keys[self.current_index][-4:] + "****"  # 마지막 4자리만 표시
            }

# 전역 서비스 키 로테이터 인스턴스
service_key_rotator = ServiceKeyRotator()