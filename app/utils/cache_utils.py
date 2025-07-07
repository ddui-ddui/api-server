from datetime import datetime, timedelta
from typing import Literal

def calculate_ttl_to_next_period(period: Literal["hour", "day", "week", "month"] = "hour") -> int:
    """
    다음 주기까지의 시간을 초 단위로 계산
    :param period: 주기 ('hour', 'day', 'week', 'month')
    :return: 다음 주기까지의 초
    """
    now = datetime.now()
    
    if period == "hour":
        # 다음 정각까지
        next_period = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    elif period == "day":
        # 다음 날 자정까지
        next_period = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        # 다음 주 월요일 자정까지
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:  # 오늘이 월요일이면 다음 주 월요일
            days_until_monday = 7
        next_period = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        # 다음 달 1일 자정까지
        if now.month == 12:
            next_period = datetime(now.year + 1, 1, 1, 0, 0, 0)
        else:
            next_period = datetime(now.year, now.month + 1, 1, 0, 0, 0)
    else:
        raise ValueError(f"지원하지 않는 주기입니다: {period}")
    
    ttl_seconds = int((next_period - now).total_seconds())
    return ttl_seconds

def calculate_ttl_with_custom_hours(hours: int) -> int:
    """
    지정된 시간 후까지의 TTL을 계산
    :param hours: 시간 수
    :return: 지정된 시간까지의 초
    """
    return hours * 3600


def calculate_ttl_to_next_mid_forecast() -> int:
    """
    다음 중기예보 발표 시간까지의 TTL 계산
    중기예보는 매일 06시, 18시에 발표됨
    """
    now = datetime.now()
    current_hour = now.hour
    
    # 다음 발표 시간 계산
    if current_hour < 6:
        # 오늘 06시까지
        next_forecast_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    elif current_hour < 18:
        # 오늘 18시까지
        next_forecast_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
    else:
        # 내일 06시까지
        tomorrow = now + timedelta(days=1)
        next_forecast_time = tomorrow.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # TTL 계산 (초 단위)
    ttl_seconds = int((next_forecast_time - now).total_seconds())
    
    # 최소 60초는 보장
    return max(ttl_seconds, 60)

def calculate_ttl_to_next_short_forecast() -> int:
    """
    다음 단기예보 발표 시간까지의 TTL 계산
    단기예보는 매일 02, 05, 08, 11, 14, 17, 20, 23시에 발표됨
    """
    now = datetime.now()
    current_hour = now.hour
    
    # 단기예보 발표 시간 (3시간 간격)
    base_times = [2, 5, 8, 11, 14, 17, 20, 23]
    
    # 다음 발표 시간 찾기
    next_base_time = None
    for t in base_times:
        if t > current_hour:
            next_base_time = t
            break
    
    if next_base_time is None:
        # 오늘 발표 시간이 모두 지났으면 내일 02시
        tomorrow = now + timedelta(days=1)
        next_forecast_time = tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
    else:
        # 오늘 중 다음 발표 시간
        next_forecast_time = now.replace(hour=next_base_time, minute=0, second=0, microsecond=0)
    
    # TTL 계산 (초 단위)
    ttl_seconds = int((next_forecast_time - now).total_seconds())
    
    # 최소 60초는 보장
    return max(ttl_seconds, 60)
