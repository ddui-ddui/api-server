import json
import os
from typing import Dict, List, Any, Union, Tuple
from app.utils.temperature_calculator import  calculate_temperature_score, calculate_temperature_sensitive_score, calculate_temperature_coat_score
from app.utils.airquality_calculator import calculate_air_quality_score, calculate_air_quality_sensitive_score
from app.config.logging_config import get_logger
logger = get_logger()

class WalkabilityCalculator:     
    def calculate_walkability_score(self, 
                                   temperature: float, 
                                   pm10_grade: int, 
                                   pm10_value: int, 
                                   pm25_grade: int,
                                   pm25_value: int,
                                   precipitation_type: int, 
                                   sky_condition: int,
                                   dog_size: str = "medium",
                                   air_quality_type: str = "korean",
                                   sensitivities: list = None,
                                   coat_type: str = "double",
                                   coat_length: str = "long") -> Dict[str, Any]:
        # 기온 계산
        temperature_score = calculate_temperature_score(temperature, dog_size)
        # 기온 민감군 점수 계산
        temperature_sensitive_score = calculate_temperature_sensitive_score(temperature, dog_size, sensitivities)
        # 기온에 따른 모피 보정
        temperature_coat_score = calculate_temperature_coat_score(temperature, dog_size, coat_type, coat_length)
        temperature_final_score = temperature_score - temperature_sensitive_score - temperature_coat_score
        logger.info(f"Temperature Score: {temperature_score}"
              f", Temperature Sensitive Score: {temperature_sensitive_score}, "
              f"Temperature Coat Score: {temperature_coat_score}"
              f", Temperature Final Score: {temperature_final_score}")

        # 대기질 계산
        air_quality_score = calculate_air_quality_score(pm10_grade, pm10_value, pm25_grade, pm25_value, air_quality_type)
        # 미세먼지 민감군 점수 계산
        air_quality_sensitive_score = calculate_air_quality_sensitive_score(pm10_grade, pm10_value, pm25_grade, pm25_value, sensitivities, air_quality_type)
        air_quality_final_score = air_quality_score - air_quality_sensitive_score  
        logger.info(f"Air Quality Score: {air_quality_score}, "
              f"Air Quality Sensitive Score: {air_quality_sensitive_score}, "
              f"Air Quality Final Score: {air_quality_final_score}")
        
        combined_score = round((temperature_final_score * 0.6) + (air_quality_final_score * 0.4))
        logger.info(f"Final Score: {combined_score}")
        walkability_score = round(max(0, min(100, combined_score)))

        if walkability_score >= 80:
            walkability_grade = 1
        elif walkability_score >= 60:
            walkability_grade = 2
        elif walkability_score >= 40:
            walkability_grade = 3
        elif walkability_score >= 20:
            walkability_grade = 4
        else:
            walkability_grade = 5

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