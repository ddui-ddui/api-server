import json
import os
from typing import Dict

def _load_json_data(filename: str) -> Dict:
    file_path = os.path.join('app', 'assets', 'walkability', filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
temperature_data = _load_json_data('temperature.json')

def calculate_temperature_score(temperature: float, dog_size: str) -> int:
    """
    기온에 따른 점수 계산
    :param temperature: 기온
    :param dog_size: 강아지 크기 (small, medium, large)
    :return: 기온 점수
    """
    temp_ranges = temperature_data.get("temperature", {}).get(dog_size, [])

    for temp_range in temp_ranges:
        if temp_range["min"] <= temperature <= temp_range["max"]:
            return temp_range["score"]
    return 3