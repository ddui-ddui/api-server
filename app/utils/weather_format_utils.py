directions = [
        "북", "북북동", "북동", "동북동", "동", "동남동", "남동", "남남동",
        "남", "남남서", "남서", "서남서", "서", "서북서", "북서", "북북서"
]

def get_wind_direction(degree: int) -> str:
    print(degree)
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