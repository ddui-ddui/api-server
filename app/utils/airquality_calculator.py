from app.utils.load_to_json import load_json_data
from app.config.logging_config import get_logger
from app.models.walkability import DogSize, CoatType, CoatLength, AirQualityType
logger = get_logger()

# 대기질 관련 데이터 로드
AIR_QUALITY_DATA = load_json_data('air_quality.json', 'app', 'assets', 'walkability')
AIR_QUALITY_SENSITIVE = load_json_data('air_quality_sensitive.json', 'app', 'assets', 'walkability')

def calculate_individual_air_quality_score(pm10_value: int, pm25_value: int, standard: AirQualityType = AirQualityType.who) -> int:
    """
    대기질에 따른 점수 계산 (1-5)
    :param pm10_value: 미세먼지 농도
    :param pm25_value: 초미세먼지 농도
    :param standard: 기준 (korean_standard 또는 who_standard)
    :return: 대기질 점수 (pm25, pm10)
    """
    # 대기질 기준 설정
    return _calculate_air_quality_score_by_value(pm10_value, pm25_value, standard)

def calculate_combined_air_quality_score(pm10_grade: int, pm10_value: int, pm25_grade: int, pm25_value: int, standard: AirQualityType = AirQualityType.who) -> int:
    """
    대기질에 따른 점수 계산 (1-5)
    :param pm10_grade: 미세먼지 등급 (1-4(최대 8))
    :param pm25_grade: 초미세먼지 등급 (1-4(최대 8))
    :param standard: 기준 (korean_standard 또는 who_standard)
    :return: 대기질 점수 (1: 최적, 5: 매우 부적합)
    """
    # 대기질 기준 설정
    # 농도가 있을때, 없을때
    if pm10_value > 0 or pm25_value > 0:
        return _calculate_air_quality_score_avg_by_value(pm10_value, pm25_value, standard)
    else:
        return _calculate_air_quality_score_avg_by_grade(pm10_grade, pm25_grade, standard)
    
def calculate_air_quality_score(pm10_grade: int = 0, pm10_value: int = 0, pm25_grade: int = 0, pm25_value: int = 0, standard: AirQualityType = AirQualityType.who) -> int:
    """
    대기질에 따른 점수 계산 (1-5)
    :param pm10_grade: 미세먼지 등급 (1-4(최대 8))
    :param pm10_value: 미세먼지 농도
    :param pm25_grade: 초미세먼지 등급 (1-4(최대 8))
    :param pm25_value: 초미세먼지 농도
    :param standard: 기준 (korean_standard 또는 who_standard)
    :return: 대기질 점수 (100: 최적, 0: 매우 부적합)
    """
    # 대기질 기준 설정
    
    # 농도가 있을때, 없을때
    if pm10_value > 0 or pm25_value > 0:
        grade = _calculate_air_quality_score_avg_by_value(pm10_value, pm25_value, standard)
    else:
        grade = _calculate_air_quality_score_avg_by_grade(pm10_grade, pm25_grade, standard)
    
    if standard == "korean_standard":
        korean_to_score = {1: 100, 2: 70, 3: 50, 4: 30} # 한국등급 별 점수
        return korean_to_score.get(grade, 70)
    else:
        who_to_score = {1: 100, 2: 85, 3: 70, 4: 55, 5: 40, 6: 25, 7: 10, 8: 0} # WHO등급 별 점수
        return who_to_score.get(grade, 55)
    
def _calculate_air_quality_score_avg_by_value(pm10_value: int, pm25_value: int, standard: str) -> int:
    """
    미세먼지 농도 수치로 대기질 점수 계산
    """
    pm10_ranges = AIR_QUALITY_DATA.get("air_quality", {}).get(standard, {}).get("pm10", [])
    pm25_ranges = AIR_QUALITY_DATA.get("air_quality", {}).get(standard, {}).get("pm25", [])
    
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
    if pm25_score >= pm10_score: # 초미세가 더 높은 경우 초미세 등급 사용
        return pm25_score
    elif pm10_score - pm25_score >= 2: # pm10이 2 이상 높은 경우 pm10 등급 사용
        return pm10_score
    else:
        return max(pm25_score, round((pm10_score * 0.45 + pm25_score * 0.55))) # 등급이 비슷한 경우 가중치 적용
    
    
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
    pm10_ranges = AIR_QUALITY_DATA.get("air_quality", {}).get(standard, {}).get("pm10", [])
    pm25_ranges = AIR_QUALITY_DATA.get("air_quality", {}).get(standard, {}).get("pm25", [])
    
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

def calculate_air_quality_sensitive_score(pm10_grade: int, pm10_value: int, pm25_grade: int, pm25_value: int, sensitivities, standard: str) -> int:
    """
    대기질 민감군에 따른 점수 계산 (1-5)
    :param pm10_grade: 미세먼지 등급 (1-4(최대 8))
    :param pm10_value: 미세먼지 농도
    :param pm25_grade: 초미세먼지 등급 (1-4(최대 8))
    :param pm25_value: 초미세먼지 농도
    :param standard: 기준 (korean_standard 또는 who_standard)
    :return: 대기질 민감군 점수 (1: 최적, 5: 매우 부적합)
    """

    # 한국 등급을 대표 수치로 변환
    korean_grade_to_value = {
        1: {"pm25": 7, "pm10": 15},    # 좋음: 0-15 → 7, 0-30 → 15
        2: {"pm25": 25, "pm10": 55},   # 보통: 16-35 → 25, 31-80 → 55
        3: {"pm25": 55, "pm10": 115},  # 나쁨: 36-75 → 55, 81-150 → 115
        4: {"pm25": 85, "pm10": 175}   # 매우나쁨: 76+ → 85, 151+ → 175
    }
    
    # WHO 등급을 대표 수치로 변환
    who_grade_to_value = {
        1: {"pm25": 2, "pm10": 7},     # 0-5 → 2, 0-15 → 7
        2: {"pm25": 8, "pm10": 23},    # 6-10 → 8, 16-30 → 23
        3: {"pm25": 13, "pm10": 38},   # 11-15 → 13, 31-45 → 38
        4: {"pm25": 20, "pm10": 53},   # 16-25 → 20, 46-60 → 53
        5: {"pm25": 30, "pm10": 70},   # 26-35 → 30, 61-80 → 70
        6: {"pm25": 43, "pm10": 90},   # 36-50 → 43, 81-100 → 90
        7: {"pm25": 63, "pm10": 125},  # 51-75 → 63, 101-150 → 125
        8: {"pm25": 85, "pm10": 200}   # 76+ → 85, 151+ → 200
    }

    # 등급은 한국 기준으로만 가능 4등급만을 제공하기 때문
    if pm25_value <= 0 and pm25_grade > 0:
        pm25_value = korean_grade_to_value.get(pm25_grade, {}).get("pm25", 0)
    if pm10_value <= 0 and pm10_grade > 0:
        pm10_value = korean_grade_to_value.get(pm10_grade, {}).get("pm10", 0)
    
    priority_weights = {
        1: 1.0,   # 100% - respiratory
        2: 0.8,   # 80% - brachycephalic
        3: 0.6,   # 60% - puppy/senior
        4: 0.4,   # 40% - heart_disease
    }    

    pm25_sensitive_total = 0
    pm10_sensitive_total = 0
    air_quality_data = AIR_QUALITY_SENSITIVE["air_quality"][standard]

    logger.info(f"현재 미세먼지 수치/등급 PM2.5 Value: {pm25_value}, PM10 Value: {pm10_value}"
          f", PM2.5 Grade: {pm25_grade}, PM10 Grade: {pm10_grade}")
    # PM2.5 민감군 점수 계산
    pm25_scores = []
    for group in sensitivities:
        if group in air_quality_data["pm25"]:
            group_data = air_quality_data["pm25"][group]
            for threshold in group_data["thresholds"]:
                if threshold["min"] <= pm25_value <= threshold["max"]:
                    pm25_scores.append({
                        'group': group,
                        'score': threshold["grade"],
                        'priority': group_data.get("priority", 5)
                    })
                    break
    # PM10 민감군 점수 계산
    pm10_scores = []
    for group in sensitivities:
        if group in air_quality_data["pm10"]:
            group_data = air_quality_data["pm10"][group]
            for threshold in group_data["thresholds"]:
                if threshold["min"] <= pm10_value <= threshold["max"]:
                    pm10_scores.append({
                        'group': group,
                        'score': threshold["grade"],
                        'priority': group_data.get("priority", 5)
                    })
                    break
    # PM2.5 가중합 계산
    if pm25_scores:
        for score_info in pm25_scores:
            weight = priority_weights.get(score_info['priority'], 0.1)
            pm25_sensitive_total += score_info['score'] * weight
    
    # PM10 가중합 계산
    if pm10_scores:
        for score_info in pm10_scores:
            weight = priority_weights.get(score_info['priority'], 0.1)
            pm10_sensitive_total += score_info['score'] * weight

    # PM2.5와 PM10 점수를 가중 평균 (PM2.5에 더 높은 가중치)
    pm25_weight = 0.60
    pm10_weight = 0.40

    air_quality_sensitive_score = (pm25_sensitive_total * pm25_weight) + (pm10_sensitive_total * pm10_weight)

    return int(air_quality_sensitive_score * 5)

def convert_grade_to_value_for_week(grade: str, air_quality_type: str) -> int:
    """
    기상청 문서 기준
    초미세먼지 일평균 농도 "낮음"은 PM2.5 농도 0∼35 ㎍/㎥이며, "높음"은 PM2.5 농도 36 ㎍/㎥ 이상입니다.
    :param grade: 등급
    :return: 등급 점수
    """    
    if air_quality_type == "korean_standard":
        if grade == "낮음": # 좋음 수준으로 반환
            return 2
        elif grade == "높음": # 나쁨 수준으로 반환
                return 3
    elif air_quality_type == "who_standard":
        if grade == "낮음":
            return 2 # 보통 수준으로 반환
        elif grade == "높음":
            return 5 # 나쁨 수준으로 반환
    
def convert_grade_to_value_for_hour(grade):
    if grade == "좋음":
        return 1
    elif grade == "보통":
        return 2
    elif grade == "나쁨":
        return 3
    elif grade == "매우나쁨":
        return 4
    return 2


# "base_grades": [
#     { "min": 0, "max": 15, "grade": 0 },
#     { "min": 16, "max": 35, "grade": 2 },
#     { "min": 36, "max": 75, "grade": 4 },
#     { "min": 76, "max": 999, "grade": 6 }
# ],
# "base_grades": [
#     { "min": 0, "max": 5, "grade": 0 },
#     { "min": 6, "max": 10, "grade": 1 },
#     { "min": 11, "max": 15, "grade": 2 },
#     { "min": 16, "max": 25, "grade": 3 },
#     { "min": 26, "max": 35, "grade": 4 },
#     { "min": 36, "max": 50, "grade": 5 },
#     { "min": 51, "max": 75, "grade": 6 },
#     { "min": 76, "max": 999, "grade": 7 }
# ]