from typing import List
from app.utils.load_to_json import load_json_data
from app.config.logging_config import get_logger
logger = get_logger()
    
TEMPERATURE_DATA = load_json_data('temperature.json', 'app', 'assets', 'walkability')
TEMPERATURE_SENSITIVE = load_json_data('temperature_sensitive.json', 'app', 'assets', 'walkability')
TEMPERATURE_COAT = load_json_data('temperature_coat.json', 'app', 'assets', 'walkability')

def calculate_temperature_score(temperature: float, dog_size: str) -> int:
    """
    기온에 따른 점수 계산
    :param temperature: 기온
    :param dog_size: 강아지 크기 (small, medium, large)
    :return: 기온 점수
    """
    temperature_ranges = TEMPERATURE_DATA.get("temperature", {}).get(dog_size, [])

    for temp_range in temperature_ranges:
        if temp_range["min"] <= temperature <= temp_range["max"]:
            grade = temp_range["grade"]
            grade_to_score_map = {1: 100, 2: 80, 3: 60, 4: 50, 5: 40}
            return grade_to_score_map.get(grade, 60)
    
    return 60


def calculate_temperature_sensitive_score(temperature: float, dog_size: str, sensitivities: List) -> int:
    """
    온도 민감군 점수 계산
    :param temperature: 현재 온도
    :param dog_size: 개 사이즈
    :param sensitivities: 민감군 리스트 ['puppy', 'senior', 'heart_disease', 'brachycephalic', 'obesity']
    :return: 민감군 보정 등급
    """
    if not sensitivities:
        return 0
    
    sensitive_scores = []
    for group in sensitivities:
        if group in TEMPERATURE_SENSITIVE:
            group_data = TEMPERATURE_SENSITIVE[group]
            size_data = group_data.get(dog_size, group_data.get("medium", []))
            
            # 온도 범위에 따른 민감군 등급 찾기
            for temp_range in size_data:
                if temp_range["min"] <= temperature <= temp_range["max"]:
                    sensitive_scores.append({
                        'group': group,
                        'score': temp_range["grade"],
                        'priority': group_data.get("priority", 5)
                    })
                    break
    
    if not sensitive_scores:
        return 0
    
    # 우선순위로 정렬
    sensitive_scores.sort(key=lambda x: x['priority'])

    # 우선순위에 따른 가중치
    # puppy: 100%, heart_disease: 80%, senior: 60%, brachycephalic: 40%, obesity: 20%
    priority_weights = {
        1: 1.0,
        2: 0.8,
        3: 0.6,
        4: 0.4,
        5: 0.2 
    }

    total_score = 0
    for score_info in sensitive_scores:
        weight = priority_weights.get(score_info['priority'], 0.1)
        total_score += score_info['score'] * weight
    
    return int(total_score * 5) # 배율 설정 

def calculate_temperature_coat_score(temperature: float, dog_size: str, coat_type: str, coat_length: str) -> int:
    """
    털에 따른 기온 점수 계산
    :param temperature: 현재 기온
    :param dog_size: 개 사이즈 (small, medium, large)
    :param coat_type: 털 종류 (single, double)
    :param coat_length: 털 길이 (short, long)
    :return: 털에 따른 기온 점수
    """
    coat_type_data = TEMPERATURE_COAT.get("type", {}).get(dog_size, {}).get(coat_type, {})
    coat_length_data = TEMPERATURE_COAT.get("length", {}).get(dog_size, {}).get(coat_length, {})

    type_grade = None
    length_grade = None
    for coat_range in coat_type_data:
        # 털 종류에 따른 범위 확인
        if coat_range["min"] <= temperature <= coat_range["max"]:
            type_grade = coat_range["grade"]
    
    for coat_range in coat_length_data:
        # 털 길이에 따른 범위 확인
        if coat_range["min"] <= temperature <= coat_range["max"]:
            length_grade = coat_range["grade"]

    # 등급별 점수 매칭
    grade_to_score_map = {1: 1.0, 2: 2.0}

    # 털 종류 혹은 길이 값은 None이 될 수 있음
    if type_grade is not None and length_grade is not None:
        # 털 종류와 길이에 따른 점수 계산
        type_score = grade_to_score_map.get(type_grade, 0)
        length_score = grade_to_score_map.get(length_grade, 0)

        total_score = (type_score * 0.4) + (length_score * 0.6)
        return int(total_score * 3)
    elif type_grade is not None:
        type_score = grade_to_score_map.get(type_grade, 0)
        return int(type_score * 3)
    elif length_grade is not None:
        length_score = grade_to_score_map.get(length_grade, 0)
        return int(length_score * 3)
    else:
        return 0

def calculate_apparent_temperature(temperature: float, humidity: int = None, 
                                 wind_speed: float = None) -> float:
    """
    종합 체감온도 계산
    :param temperature: 현재 기온 (섭씨)
    :param humidity: 상대습도 (%)
    :param wind_speed: 풍속 (m/s)
    :return: 체감온도 정보
    """
    apparent_temperature = temperature
    # 겨울철 바람냉각 (기온 10도 이하, 풍속 1.34m/s 이상)
    if temperature <= 10 and wind_speed and wind_speed >= 1.34:
        wind_chill = calculate_wind_chill(temperature, wind_speed)
        apparent_temperature = round(wind_chill, 1)
    
    # 여름철 열지수 (기온 27도 이상, 습도 40% 이상)
    elif temperature >= 27 and humidity and humidity >= 40:
        heat_index = calculate_heat_index(temperature, humidity)
        if heat_index > temperature:
            apparent_temperature = round(heat_index, 1)

    return apparent_temperature

def calculate_heat_index(temperature: float, humidity: float) -> float:
    """
    Heat Index 계산 (여름철 체감온도)
    :param temperature: 기온 (섭씨)
    :param humidity: 상대습도 (%)
    :return: 체감온도 (섭씨)
    """
    # 섭씨를 화씨로 변환
    temp_f = temperature * 9/5 + 32
    
    if temp_f < 80 or humidity < 40:
        return temperature  # Heat Index 적용 조건 미충족
    
    # Heat Index 공식
    hi = (-42.379 + 
          2.04901523 * temp_f + 
          10.14333127 * humidity - 
          0.22475541 * temp_f * humidity - 
          6.83783e-3 * temp_f**2 - 
          5.481717e-2 * humidity**2 + 
          1.22874e-3 * temp_f**2 * humidity + 
          8.5282e-4 * temp_f * humidity**2 - 
          1.99e-6 * temp_f**2 * humidity**2)
    
    # 화씨를 섭씨로 변환
    return (hi - 32) * 5/9

def calculate_wind_chill(temperature: float, wind_speed: float) -> float:
    """
    Wind Chill 계산 (겨울철 체감온도)
    :param temperature: 기온 (섭씨)
    :param wind_speed: 풍속 (m/s)
    :return: 체감온도 (섭씨)
    """
    if temperature > 10 or wind_speed < 1.34:  # 적용 조건
        return temperature
    
    # m/s를 km/h로 변환
    wind_kmh = wind_speed * 3.6
    
    wind_chill = (13.12 + 0.6215 * temperature - 
                  11.37 * (wind_kmh ** 0.16) + 
                  0.3965 * temperature * (wind_kmh ** 0.16))
    
    return wind_chill


# def calculate_temperature_score(temperature: float, dog_size: str) -> int:
#     """
#     기온에 따른 점수 계산
#     :param temperature: 기온
#     :param dog_size: 강아지 크기 (small, medium, large)
#     :return: 기온 점수
#     """
#     temp_ranges = TEMPERATURE_DATA.get("temperature", {}).get(dog_size, [])

#     for temp_range in temp_ranges:
#         if temp_range["min"] <= temperature <= temp_range["max"]:
#             return temp_range["grade"]
#     return 2

# def calculate_temperature_sensitive_score(self, temperature: float, dog_size: str, sensitivities: List[str]) -> int:
#     """
#     온도 민감군 점수 계산
#     :param temperature: 현재 온도
#     :param dog_size: 개 사이즈
#     :param sensitivities: 민감군 리스트 ['puppy', 'senior', 'heart_disease', 'brachycephalic', 'obesity']
#     :return: 민감군 보정 등급
#     """
#     if not sensitivities:
#         return 0
    
#     sensitive_scores = []
    
#     # 각 민감군별 점수 계산
#     for group in sensitivities:
#         if group in TEMPERATURE_SENSITIVE:
#             group_data = TEMPERATURE_SENSITIVE[group]
#             size_data = group_data.get(dog_size, group_data.get("medium", []))
            
#             # 온도 범위에 따른 민감군 등급 찾기
#             for temp_range in size_data:
#                 if temp_range["min"] <= temperature <= temp_range["max"]:
#                     sensitive_scores.append({
#                         'group': group,
#                         'score': temp_range["grade"],
#                         'priority': group_data.get("priority", 5)
#                     })
#                     break
    
#     if not sensitive_scores:
#         return 0
    
#     # 우선순위로 정렬
#     sensitive_scores.sort(key=lambda x: x['priority'])

#     priority_weights = {
#         1: 1.0,   # 100% - 6개월 미만
#         2: 0.8,   # 80% - 심장병
#         3: 0.6,   # 60% - 노견  
#         4: 0.4,   # 40% - 단두종
#         5: 0.2    # 20% - 비만
#     }
#     total_score = 0
#     for score_info in sensitive_scores:
#         weight = priority_weights.get(score_info['priority'], 0.1)
#         total_score += score_info['score'] * weight
    
#     return int(total_score)