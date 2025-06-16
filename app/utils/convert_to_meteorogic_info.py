import pandas as pd
import json
from pathlib import Path
from app.config.logging_config import get_logger
logger = get_logger()

def convert_excel_to_json():
    """
    lat_lon.xlsx 파일을 읽어서 weather_service_code.json으로 변환
    """
    # 파일 경로 설정
    current_dir = Path(__file__).parent
    assets_path = current_dir / "app" / "assets" / "zone"
    excel_file = assets_path / "lat_lon.xlsx"
    json_file = assets_path / "weather_service_code.json"
    
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(excel_file)
        
        # 데이터 구조 확인
        # print("엑셀 파일 구조:")
        # print(f"컬럼명: {list(df.columns)}")
        # print(f"데이터 타입: {df.dtypes}")
        # print("\n처음 3행 데이터:")
        # print(df.head(3))
        
        # 데이터프레임을 딕셔너리 리스트로 변환
        data = []
        for _, row in df.iterrows():
            try:
                # iloc를 사용하여 위치 기반 접근
                region_data = {
                    "reg_id": int(row.iloc[0]) if pd.notna(row.iloc[0]) else None,
                    "region": str(row.iloc[1]) if pd.notna(row.iloc[1]) else "",
                    "meteorological": str(row.iloc[4]) if pd.notna(row.iloc[4]) else "",
                    "lat": float(row.iloc[2]) if pd.notna(row.iloc[3]) else None,
                    "lon": float(row.iloc[3]) if pd.notna(row.iloc[4]) else None,
                    "meteorological_lat": float(row.iloc[5]) if pd.notna(row.iloc[5]) else None,
                    "meteorological_lon": float(row.iloc[6]) if pd.notna(row.iloc[6]) else None
                }
                data.append(region_data)
                logger.info(f"성공 처리: {region_data['region']}")
            except (ValueError, IndexError) as e:
                logger.info(f"행 처리 오류: {row.values}, 오류: {e}")
                continue
        
        # JSON 파일로 저장
        logger.info(f"\nJSON 파일 저장 중: {json_file}")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"변환 완료! 총 {len(data)}개의 지역 데이터가 저장되었습니다.")
        logger.info(f"저장 위치: {json_file}")
        
        # 샘플 데이터 출력
        if data:
            logger.info("\n샘플 데이터:")
            for i, sample in enumerate(data[:3]):
                logger.info(f"{i+1}. {sample}")
        
    except FileNotFoundError:
        logger.error(f"엑셀 파일을 찾을 수 없습니다: {excel_file}")
        logger.error("파일 경로를 확인해주세요.")
    except Exception as e:
        logger.error(f"오류 발생: {e}")

if __name__ == "__main__":
    convert_excel_to_json()