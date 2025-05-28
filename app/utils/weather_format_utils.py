from typing import Dict
import re


directions = [
        "북", "북북동", "북동", "동북동", "동", "동남동", "남동", "남남동",
        "남", "남남서", "남서", "서남서", "서", "서북서", "북서", "북북서"
]

def get_wind_direction(degree: int) -> str:
    try:
        degree = int(degree)
    except (ValueError, TypeError):
        return "알 수 없음"
    
    index = int((degree + 22.5 * 0.5) / 22.5)
    return directions[index]

def convert_wind_speed(speed: float, type:str) -> float:
    """
    풍속값을 m/s로 변환합니다.
    :param speed: 풍속값
    :param type: 풍속값의 단위 (m/s, km/h, mph)
    :return: 변환된 문자열 풍속값 (m/s)
    """
    if type == "m/s":
        return speed
    elif type == "km/h":
        return speed / 3.6
    elif type == "mph":
        return speed * 0.44704
    else:
        raise ValueError("풍속 단위는 m/s, km/h, mph 중 하나여야 합니다.")

def convert_weather_condition(condition)-> Dict[str, int]:
    """
    중기예보 문자열을 코드로 변환
    
    기본 하늘상태:
    1: 맑음
    3: 구름많음
    4: 흐림
    
    강수 유형(precipitation_type):
    0: 없음
    1: 비
    2: 비/눈
    3: 눈
    4: 소나기
    """
    if not condition:
        return {"sky_condition": 0, "precipitation_type": 0}
    
    # 기본 하늘 상태 확인
    if "맑음" in condition:
        sky = 1
    elif "구름많" in condition:
        sky = 3
    elif "흐림" in condition or "흐리" in condition:
        sky = 4
    else:
        sky = 0
    
    # 강수 유형 확인
    if "비" in condition and "눈" in condition:
        precip = 2  # 비/눈
    elif "눈" in condition:
        precip = 3  # 눈
    elif "소나기" in condition:
        precip = 4  # 소나기
    elif "비" in condition:
        precip = 1  # 비
    else:
        precip = 0  # 없음
    
    return {"sky_condition": sky, "precipitation_type": precip}


def parse_rainfall(value) -> float:
    """
    강수량 값을 파싱하여 float로 변환
    :param value: 강수량 값 (숫자 또는 "강수없음" 등의 문자열)
    :return: 강수량 (float)
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        if "강수없음" in value or "미만" in value or value.strip() == "":
            return 0.0
        
        try:
            numbers = re.findall(r'[\d.]+', value)
            if numbers:
                return float(numbers[0])
            return 0.0
        except (ValueError, IndexError):
            return 0.0
    
    return 0.0