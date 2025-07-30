from datetime import datetime
from typing import Dict, Any
from app.utils.temperature_calculator import  calculate_temperature_score, calculate_temperature_sensitive_score, calculate_temperature_coat_score
from app.utils.airquality_calculator import calculate_air_quality_score, calculate_air_quality_sensitive_score
from app.utils.load_to_json import load_json_data
from app.config.logging_config import get_logger
logger = get_logger()

OOTD_TEMPERATURE = load_json_data('ootd_sentence.json', 'app', 'assets', 'walkability')
WALKABILITY_SENTENCES_GRADES = load_json_data('walkability_sentence.json', 'app', 'assets', 'walkability')
RAIN_PRECIPITATION_TYPES = [1, 2, 5, 6]

class WalkabilityCalculator:     
    def calculate_walkability_score(self, 
                                   temperature: float, 
                                   pm10_grade: int, 
                                   pm10_value: int, 
                                   pm25_grade: int,
                                   pm25_value: int,
                                   precipitation_type: int, 
                                   sky_condition: int,
                                   precipitation_amount: float,
                                   precipitation_probability: int,
                                   dog_size: str = "medium",
                                   air_quality_type: str = "korean",
                                   sensitivities: list = None,
                                   coat_type: str = "double",
                                   coat_length: str = "long") -> Dict[str, Any]:
        
        try:
            # 비가 오는 경우 나쁨으로 표시
            if precipitation_amount >= 5.0 or precipitation_probability >= 80:
                logger.info(f"강수량과 강수 확률이 기준치에 도달하여 지수 나쁨으로 반환.")
                logger.info(f"강수량: {precipitation_amount}, 강수 확률(퍼센트): {precipitation_probability}")
                return {
                "walkability_score": 20,
                "walkability_grade": 2,
            }

            # 31도 이상, 7월 8월, 하늘 상태 맑음, 현재 시간이 9시부터 5시 사이인 경우 나쁨으로 반환
            current_hour = datetime.now().hour
            current_month = datetime.now().month
            if temperature >= 31 and sky_condition == 1 and current_month in [7, 8] and 9 <= current_hour <= 17:
                sky_condition_str = "맑음" if sky_condition == 1 else "흐림" if sky_condition == 4 else "구름많음"
                logger.info(f"폭염 기준에 도달하여 산책 지수 나쁨으로 반환.")
                logger.info(f"현재 시간: {current_hour}시, 현재 월: {current_month}, 기온: {temperature}도, 하늘 상태: {sky_condition_str}")
                return {
                    "walkability_score": 20,
                    "walkability_grade": 2,
                }

            # 기온 계산
            temperature_score = calculate_temperature_score(temperature, dog_size)
            # 기온 민감군 점수 계산
            temperature_sensitive_score = calculate_temperature_sensitive_score(temperature, dog_size, sensitivities)
            # 기온에 따른 모피 보정
            temperature_coat_score = calculate_temperature_coat_score(temperature, dog_size, coat_type, coat_length)
            temperature_final_score = temperature_score - temperature_sensitive_score - temperature_coat_score
            # logger.info(f"Temperature Score: {temperature_score}"
            #     f", Temperature Sensitive Score: {temperature_sensitive_score}, "
            #     f"Temperature Coat Score: {temperature_coat_score}"
            #     f", Temperature Final Score: {temperature_final_score}")

            # 대기질 계산
            air_quality_score = calculate_air_quality_score(pm10_grade, pm10_value, pm25_grade, pm25_value, air_quality_type)
            # 미세먼지 민감군 점수 계산
            air_quality_sensitive_score = calculate_air_quality_sensitive_score(pm10_grade, pm10_value, pm25_grade, pm25_value, sensitivities, air_quality_type)
            air_quality_final_score = air_quality_score - air_quality_sensitive_score  
            # logger.info(f"Air Quality Score: {air_quality_score}, "
            #     f"Air Quality Sensitive Score: {air_quality_sensitive_score}, "
            #     f"Air Quality Final Score: {air_quality_final_score}")
            
            combined_score = round((temperature_final_score * 0.6) + (air_quality_final_score * 0.4))
            # logger.info(f"기온 최종 점수: {temperature_final_score}, 대기질 최종 점수: {air_quality_final_score}")
            # logger.info(f"가중치 별 점수 - 기온: {round(temperature_final_score * 0.6)}, 대기질: {round(air_quality_final_score * 0.4)}")
            # logger.info(f"최종 점수: {combined_score}")
            walkability_score = round(max(0, min(100, combined_score)))
            
            # 프론트에서 내림 차순으로 등급 매김
            if walkability_score >= 80:
                walkability_grade = 5
            elif walkability_score >= 60:
                walkability_grade = 4
            elif walkability_score >= 40:
                walkability_grade = 3
            elif walkability_score >= 20:
                walkability_grade = 2
            elif walkability_score >= 0:
                walkability_grade = 1
            else:
                walkability_grade = 6

            return {
                "walkability_score": walkability_score,
                "walkability_grade": walkability_grade,
            }
        except Exception as e:
            logger.error(f"산책 지수 계산 실패: {str(e)}")
            return {
                "walkability_score": "N/A",
                "walkability_grade": -1,
            }
    
    def get_ootd_by_temperature(self, weather_data: Dict[str, Any],  walkability_grade: int, dog_size: str = "medium") -> Dict[str, Any]:
        """
        기온에 따른 OOTD 계산
        :param weather_data: 날씨 정보
        :param dog_size: 개 사이즈 (small, medium, large)
        :return: OOTD 정보
        """
        ootd_data = OOTD_TEMPERATURE.get(dog_size, {})
        walkability_sentences_data = WALKABILITY_SENTENCES_GRADES.get("sentences", {})
        ootd = None
        phrases = None
              
        for ootd in ootd_data:
            # 비오면 무조건 우비(타입 배열)
            if weather_data["precipitation_type"] in RAIN_PRECIPITATION_TYPES:
                ootd = ["우비"]
                break
            
            # 그게 아니라면 기온에 따라 OOTD 결정
            if ootd["min"] <= weather_data["temperature"] <= ootd["max"]:
                ootd = ootd["clothing"]
                break
        for items in walkability_sentences_data:
            if int(items["grade"]) == walkability_grade:
                phrases = items["clothing"]
                # break

        logger.info(f"OOTD Info: {ootd}, Phrases: {phrases}")

        ootd_info = {
            "ootd": ootd,
            "phrases": phrases
        }

        return ootd_info