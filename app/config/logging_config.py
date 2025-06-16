import logging
import logging.handlers
import os
from app.core.config import settings

def get_logger(name="DDUI-DDUI"):
    return logging.getLogger(name)

def setup_logging():

    logger = logging.getLogger("DDUI-DDUI")
    if logger.handlers:
        return logger

    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # 운영에서만 로그 파일 쌓음
    if settings.ENVIRONMENT == "production":
        # 로그 파일 쌓을 위치
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=f"{log_dir}/app.log",
            when="midnight", # 매일 자정
            interval=1, # 1일마다 새 로그 파일 생성
            backupCount=30,  # 30일간 보관
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    
    # 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger