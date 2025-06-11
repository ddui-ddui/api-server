import json
import os
from typing import Dict

def _load_json_data(filename: str) -> Dict:
    file_path = os.path.join('app', 'assets', 'walkability', filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
TEMPERATURE_DATA = _load_json_data('temperature.json')

def calculate_temperature_score(temperature: float, dog_size: str) -> int:
    """
    기온에 따른 점수 계산
    :param temperature: 기온
    :param dog_size: 강아지 크기 (small, medium, large)
    :return: 기온 점수
    """
    temp_ranges = TEMPERATURE_DATA.get("temperature", {}).get(dog_size, [])

    for temp_range in temp_ranges:
        if temp_range["min"] <= temperature <= temp_range["max"]:
            return temp_range["score"]
    return 3


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
            apparent_temperature = (heat_index, 1)
    
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