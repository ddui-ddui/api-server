import json
import math
from pathlib import Path
from app.config.logging_config import get_logger
logger = get_logger()

def _load_weather_region_codes() -> tuple[list, list, list]:
    current_dir = Path(__file__).parent
    assets_path = current_dir.parent / "assets" / "zone"
    region_file = assets_path / "weather_service_code.json"
    zone_file = assets_path / "admin_district_code.json"
    weather_forecast_file = assets_path / "weather_forecast_zone_code.json"

    if not region_file.exists():
        raise FileNotFoundError(f"Region file not found: {region_file}")
    with open(region_file, 'r', encoding='utf-8') as f:
        weather_service_codes = json.load(f)

    if not zone_file.exists():
        raise FileNotFoundError(f"Zone file not found: {zone_file}")
    with open(zone_file, 'r', encoding='utf-8') as f:
        zone_data = json.load(f)
    
    if not weather_forecast_file.exists():
        raise FileNotFoundError(f"Weather forecast file not found: {weather_forecast_file}")
    with open(weather_forecast_file, 'r', encoding='utf-8') as f:
        weather_forecast_data = json.load(f)

    return weather_service_codes, zone_data, weather_forecast_data

WEATHER_SERVICE_CODES, ZONE_DATA, WEATHER_FORECAST_DATA = _load_weather_region_codes()


def convert_grid_to_region(nx: int, ny: int) -> str:
    """
    유클리드 거리 계산을 사용하며 거리 값이 없거나
    거리가 30이상 차이나면 대전으로 설정함.
    
    기상청 격자 좌표를 지역 좌표로 변환합니다.
    :param nx: 격자 x 좌표
    :param ny: 격자 y 좌표
    :return: 지역 좌표 ID
    """
    
    closest_region = None
    min_distance = float('inf')
    
    for region in WEATHER_FORECAST_DATA:
        if "x" in region and "y" in region:
            distance = ((nx - region["x"]) ** 2 + (ny - region["y"]) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                closest_region = region
    
    # 너무 먼 거리인 경우 기본값 (대전)
    if min_distance > 10 or closest_region is None:  # 적절한 임계값 설정
        return "11C20401"
    
    return closest_region["regId"]

def convert_lat_lon_to_region_id(lat: float, lon: float) -> list:
    """
    위도와 경도를 기반으로 가장 가까운 3개 지역 코드를 반환합니다.
    가까운 순서대로 정렬하여 반환합니다.
    
    :param lat: 위도
    :param lon: 경도
    :return: 가까운 순서대로 정렬된 3개 지역의 정보 리스트
    """
    distances = []
    
    # 위도/경도 가중치 (한국 기준으로 실제 거리 비율 적용)
    LAT_WEIGHT = 1.0      # 위도 1도 ≈ 111km
    LON_WEIGHT = 0.8      # 경도 1도 ≈ 88km (한국 위도 기준)
    
    for region in WEATHER_SERVICE_CODES:
        if "lat" in region and "lon" in region and region["lat"] is not None and region["lon"] is not None:
            lat_diff = (lat - region["lat"]) * LAT_WEIGHT
            lon_diff = (lon - region["lon"]) * LON_WEIGHT
            
            distance = math.sqrt(lat_diff**2 + lon_diff**2)
            
            distances.append({
                "region": region,
                "distance": distance
            })
    
    # 거리 기준으로 정렬 (가까운 순서)
    distances.sort(key=lambda x: x["distance"])
    
    # 상위 3개 선택
    top_3 = distances[:3]
    
    # 결과 리스트 생성
    result = []
    for i, item in enumerate(top_3):
        region_info = {
            "rank": i + 1,
            "reg_id": str(item["region"]["reg_id"]),
            "region": item["region"]["region"],
            "meteorological": item["region"]["meteorological"]
        }
        result.append(region_info)
    
    return result

def convert_lat_lon_for_region(lat: float, lon: float) -> str:
    """
    위도와 경도를 기반으로 지역 코드를 반환합니다.
    :param lat: 위도
    :param lon: 경도
    :return: 지역 코드
    """
    default_region = ZONE_DATA[0]; # 기본값: 서울 종로구
    closest_region = None
    min_distance = float('inf')
    
    try:
        for region in ZONE_DATA:
            if "latitude" in region and "longitude" in region:
                distance = ((lat - region["latitude"]) ** 2 + (lon - region["longitude"]) ** 2) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    closest_region = region

        if closest_region and 'subregion' in closest_region and closest_region['subregion']:
            return closest_region
        else:
            logger.info("지역을 찾을 수 없습니다. 기본 지역으로 설정합니다.")
            logger.info(f"요청된 위도/경도: ({lat}, {lon})")
            return default_region
    except Exception as e:
        logger.error(f"지역 변환 중 오류 발생: {str(e)}")
        logger.info(f"요청된 위도/경도: ({lat}, {lon})")
        return default_region