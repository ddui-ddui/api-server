import json
import os
from typing import Dict, List, Any, Union, Tuple
from app.utils.temperature_calculator import calculate_temperature_score
from app.utils.airquality_calculator import calculate_air_quality_score

class WalkabilityCalculator:
    def __init__(self):
        # 설정 파일 로드
        self.temperature_data = self._load_json_data('temperature.json')
        self.air_quality_data = self._load_json_data('air_quality.json')
        # 민감군 정의되면 추가해야 함
        # self.sensitive_groups_data = self._load_json_data('sensitive_groups.json')
        
    def _load_json_data(self, filename: str) -> Dict:
        file_path = os.path.join('app', 'assets', 'walkability', filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
        
    # TODO: 
    # sensitive_groups: List[str] = None)
    # 민감군 정의되면 추가해야 함
    def calculate_walkability_score(self, 
                                   temperature: float, 
                                   pm10_grade: int, 
                                   pm10_value: int, 
                                   pm25_grade: int,
                                   pm25_value: int,
                                   precipitation_type: int, 
                                   precipitation_probability: float,
                                   sky_condition: int,
                                   dog_size: str = "medium",
                                   air_quality_type: str = "korean") -> Dict[str, Any]:
        # 최고 점수
        base_score = 100
        # 기온 계산
        temp_score = calculate_temperature_score(temperature, dog_size)
        temp_deduction = self._convert_score_to_deduction(temp_score, max_deduction=40)
        
        # 대기질 계산
        air_quality_score = calculate_air_quality_score(pm10_grade, pm10_value, pm25_grade, pm25_value, air_quality_type)
        air_deduction = self._convert_score_to_deduction(air_quality_score, max_deduction=30)
        
        total_deduction = temp_deduction + air_deduction
        
        # 최종 점수 계산 (0-100 범위로 제한)
        walkability_score = round(max(0, min(100, base_score - total_deduction)))
        walkability_grade = 5 - min(4, walkability_score // 20)
        return {
            "walkability_score": walkability_score,
            "walkability_grade": walkability_grade,
        }
    
    
    def _convert_score_to_deduction(self, score: int, max_deduction: float) -> float:
        """
        점수(1-5)를 차감 점수로 변환
        :param score: 1-5 사이의 점수 (1이 가장 좋음, 5가 가장 나쁨)
        :param max_deduction: 최대 차감 점수
        :return: 차감할 점수 (음수)
        """
        if score == 1:
            return 0  # 최적 상태는 차감 없음
        elif score == 2:
            return max_deduction * 0.25  # 최대 차감의 25%
        elif score == 3:
            return max_deduction * 0.5   # 최대 차감의 50%
        elif score == 4:
            return max_deduction * 0.75  # 최대 차감의 75%
        elif score == 5:
            return max_deduction         # 최대 차감
        else:
            return 0  # 기본값