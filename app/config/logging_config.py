import logging
import logging.handlers
import os
import re
from app.core.config import settings
from app.config.context import request_id, client_ip
from app.common.logging_file_handler import create_daily_rotating_handler

class ContextFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensitive_patterns = [
            (r'(serviceKey["\']?\s*[:=]\s*["\']?)([^"\'&\s]{8,})(["\']?)', r'\1\2[:4]***\2[-4:]\3')
        ]

    def mask_sensitive_data(self, message):
        """메시지에서 민감한 정보를 마스킹 처리"""
        for pattern, replacement in self.sensitive_patterns:
            # serviceKey 값 찾기
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

    def format(self, record):
        record.request_id = request_id.get() or "System"
        record.client_ip = client_ip.get() or "System"
        
        if hasattr(record, 'msg') and record.msg:
            record.msg = self.mask_sensitive_data(str(record.msg))
        
        if record.args:
            masked_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    masked_args.append(self.mask_sensitive_data(arg))
                else:
                    masked_args.append(arg)
            record.args = tuple(masked_args)
        
        return super().format(record)

def get_logger(name="DDUI-DDUI"):
    return logging.getLogger(name)

def setup_logging():

    logger = logging.getLogger("DDUI-DDUI")
    if logger.handlers:
        return logger

    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    formatter = ContextFormatter(
        '%(asctime)s - [%(request_id)s] - %(client_ip)s - %(levelname)s - %(message)s'
    )

    # 운영에서만 로그 파일 쌓음
    if settings.ENVIRONMENT == "production":
        # 로그 파일 쌓을 위치
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = create_daily_rotating_handler(
            log_dir="logs",
            filename="app.log",
            max_size_mb=5,      # 20MB마다 로테이션
            backup_count=50      # 30개 파일 보관
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    
    # 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger