import json
import os
from typing import Dict

def _load_json_data(filename: str) -> Dict:
    file_path = os.path.join('app', 'assets', 'walkability', filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
air_quality_data = _load_json_data('air_quality.json')

def calculate_air_quality_score(pm10_value: int, pm25_value: int, standard: str = "korean") -> int:
    """
    대기질에 따른 점수 계산 (1-5)
    :param pm10_value: 미세먼지 농도
    :param pm25_value: 초미세먼지 농도
    :param standard: 기준 (korean_standard 또는 who_standard)
    :return: 대기질 점수 (1: 최적, 5: 매우 부적합)
    """
    # 대기질 기준 설정
    standard = f"{standard}_standard" if standard in ["korean", "who"] else "korean_standard"
    return _calculate_air_quality_score_by_value(pm10_value, pm25_value, standard)

def calculate_air_quality_score_avg(pm10_grade: int, pm10_value: int, pm25_grade: int, pm25_value: int, standard: str = "korean") -> int:
    """
    대기질에 따른 점수 계산 (1-5)
    :param pm10_grade: 미세먼지 등급 (1-4(최대 8))
    :param pm25_grade: 초미세먼지 등급 (1-4(최대 8))
    :param standard: 기준 (korean_standard 또는 who_standard)
    :return: 대기질 점수 (1: 최적, 5: 매우 부적합)
    """
    # 대기질 기준 설정
    standard = f"{standard}_standard" if standard in ["korean", "who"] else "korean_standard"

    # 농도가 있을때, 없을때
    if pm10_value > 0 or pm25_value > 0:
        return _calculate_air_quality_score_avg_by_value(pm10_value, pm25_value, standard)
    else:
        return _calculate_air_quality_score_avg_by_grade(pm10_grade, pm25_grade, standard)
    
    
def _calculate_air_quality_score_avg_by_value(pm10_value: int, pm25_value: int, standard: str) -> int:
    """
    미세먼지 농도 수치로 대기질 점수 계산
    """
    pm10_ranges = air_quality_data.get("air_quality", {}).get(standard, {}).get("pm10", [])
    pm25_ranges = air_quality_data.get("air_quality", {}).get(standard, {}).get("pm25", [])
    
    pm10_score = 1
    if pm10_value > 0:
        for range_info in pm10_ranges:
            if range_info["min"] <= pm10_value <= range_info["max"]:
                pm10_score = range_info["score"]
                break
    
    pm25_score = 1
    if pm25_value > 0:
        for range_info in pm25_ranges:
            if range_info["min"] <= pm25_value <= range_info["max"]:
                pm25_score = range_info["score"]
                break
    
    # 약간의 가중치
    if pm25_score >= pm10_score:
        return pm25_score
    elif pm10_score - pm25_score >= 2:
        return pm10_score
    else:
        return max(pm25_score, round((pm10_score * 0.45 + pm25_score * 0.55)))
    
    
def _calculate_air_quality_score_avg_by_grade(pm10_grade: int, pm25_grade: int, standard: str) -> int:
    """
    미세먼지 등급으로 대기질 점수 계산
    """
    if pm25_grade >= pm10_grade:
        air_quality_score = pm25_grade
    elif pm10_grade - pm25_grade >= 2:
        air_quality_score = pm10_grade
    else:
        air_quality_score = max(pm25_grade, round(pm10_grade * 0.9))
    
    if standard == "korean_standard":
        normalized_score = min(5, round(air_quality_score * 1.25))
    else:
        normalized_score = min(5, round(air_quality_score * 5 / 8))
    
    return normalized_score

def _calculate_air_quality_score_by_value(pm10_value: int, pm25_value: int, standard: str) -> int:
    """
    미세먼지 농도 수치로 대기질 점수 계산
    """
    pm10_ranges = air_quality_data.get("air_quality", {}).get(standard, {}).get("pm10", [])
    pm25_ranges = air_quality_data.get("air_quality", {}).get(standard, {}).get("pm25", [])
    
    pm10_score = 1
    if pm10_value > 0:
        for range_info in pm10_ranges:
            if range_info["min"] <= pm10_value <= range_info["max"]:
                pm10_score = range_info["score"]
                break
    
    pm25_score = 1
    if pm25_value > 0:
        for range_info in pm25_ranges:
            if range_info["min"] <= pm25_value <= range_info["max"]:
                pm25_score = range_info["score"]
                break
    
    return pm10_score, pm25_score
    