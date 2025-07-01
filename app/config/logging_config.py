from datetime import time, datetime, timedelta
import re
import sys
from loguru import logger
from app.core.config import settings
from app.config.context import request_id, client_ip

class Rotator:
    def __init__(self, size, at):
        self._size = size
        now = datetime.now()
        today_at_time = now.replace(hour=at.hour, minute=at.minute, second=at.second)
        if now >= today_at_time:
            self._next_rotate = today_at_time + timedelta(days=1)
        else:
            self._next_rotate = today_at_time

    def should_rotate(self, message, file):
        file.seek(0, 2)

        if file.tell() + len(message) > self._size:
            return True
        if message.record["time"].timestamp() > self._next_rotate.timestamp():
            self._next_rotate += timedelta(days=1)
            return True
        return False

rotator = Rotator(
    size=5 * 1024 * 1024, # 5 MB
    at=time(hour=0, minute=0, second=0)
)

# 민감한 정보 마스킹 함수
def mask_sensitive_data(message: str) -> str:
    """메시지에서 민감한 정보를 마스킹 처리"""
    sensitive_patterns = [
        (r'(serviceKey["\']?\s*[:=]\s*["\']?)([^"\'&\s]{8,})(["\']?)', r'\1\2[:4]***\2[-4:]\3')
    ]
    
    for pattern, _ in sensitive_patterns:
        matches = re.finditer(pattern, message, re.IGNORECASE)
        for match in matches:
            original_value = match.group(2)
            if len(original_value) > 8:
                masked_value = f"{original_value[:4]}***{original_value[-4:]}"
            else:
                masked_value = "***"
            
            message = message.replace(
                match.group(0), 
                match.group(1) + masked_value + (match.group(3) if len(match.groups()) >= 3 else '')
            )
    
    return message

# 커스텀 포맷터
def format_record(record):
    """로그 레코드에 컨텍스트 정보 추가"""
    record["extra"]["request_id"] = request_id.get() or "System"
    record["extra"]["client_ip"] = client_ip.get() or "System"
    
    # 민감한 정보 마스킹
    if "message" in record:
        record["message"] = mask_sensitive_data(str(record["message"]))
    
    return record

def setup_logging():
    # 기본 핸들러 제거
    logger.remove()
    
    # 로그 레벨 설정
    log_level = settings.LOG_LEVEL.upper()
    
    # 로그 포맷 정의
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <3}</level> | "
        "<cyan>[{extra[request_id]}]</cyan> | "
        "<blue>{extra[client_ip]}</blue> | "
        "<level>{message}</level>"
    )
    
    # 콘솔 핸들러 추가
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        filter=format_record
    )
    
    # 운영 환경에서만 파일 핸들러 추가
    # if settings.ENVIRONMENT == "production":
    logger.add(
        "logs/app.log",
        format=log_format,
        level=log_level,
        rotation=rotator.should_rotate,
        # retention="30 days",
        filter=format_record
    )

def get_logger():
    return logger

setup_logging()