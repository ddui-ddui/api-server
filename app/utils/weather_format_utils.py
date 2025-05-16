from typing import Dict


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



# region_maps = [
#         {"name": "서울", "code": "11B00000", "nx_range": (58, 62), "ny_range": (125, 128)},
#         {"name": "인천", "code": "11B00000", "nx_range": (53, 58), "ny_range": (120, 125)},
#         {"name": "경기도", "code": "11B00000", "nx_range": (52, 73), "ny_range": (120, 135)},
#         {"name": "강원도영서", "code": "11D10000", "nx_range": (73, 92), "ny_range": (132, 150)},
#         {"name": "강원도영동", "code": "11D20000", "nx_range": (92, 102), "ny_range": (127, 150)},
#         {"name": "대전", "code": "11C20000", "nx_range": (63, 71), "ny_range": (110, 118)},
#         {"name": "세종", "code": "11C20000", "nx_range": (63, 71), "ny_range": (118, 122)},
#         {"name": "충청북도", "code": "11C10000", "nx_range": (69, 81), "ny_range": (118, 130)},
#         {"name": "충청남도", "code": "11C20000", "nx_range": (55, 67), "ny_range": (103, 118)},
#         {"name": "전라북도", "code": "11F10000", "nx_range": (56, 74), "ny_range": (89, 105)},
#         {"name": "전라남도", "code": "11F20000", "nx_range": (50, 73), "ny_range": (70, 89)},
#         {"name": "광주", "code": "11F20000", "nx_range": (58, 61), "ny_range": (74, 76)},
#         {"name": "대구", "code": "11H10000", "nx_range": (86, 91), "ny_range": (89, 93)},
#         {"name": "경상북도", "code": "11H10000", "nx_range": (80, 100), "ny_range": (89, 130)},
#         {"name": "경상남도", "code": "11H20000", "nx_range": (74, 90), "ny_range": (70, 89)},
#         {"name": "부산", "code": "11H20000", "nx_range": (97, 102), "ny_range": (74, 78)},
#         {"name": "울산", "code": "11H20000", "nx_range": (102, 105), "ny_range": (83, 89)},
#         {"name": "제주도", "code": "11G00000", "nx_range": (52, 60), "ny_range": (38, 44)}
#     ]