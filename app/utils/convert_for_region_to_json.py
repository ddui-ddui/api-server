import pandas as pd
import json
from pathlib import Path

northern_gyeonggi = ['고양시','구리시','남양주시','동두천시','양주시','의정부시','파주시','포천시','가평군','연천군']
southern_gyeonggi = ['과천시','광명시','광주시','군포시','김포시','부천시','성남시','수원시','시흥시','안산시','안성시','안양시','여주시','오산시','용인시','의왕시','이천시','평택시','하남시','화성시','양평군']
western_gangwon = ['춘천시','원주시','홍천군','횡성군','영월군','평창군','정선군','철원군','화천군','양구군','인제군','태백시']
eastern_gangwon = ['강릉시','동해시','삼척시','속초시','고성군','양양군']

def make_provinces():
    current_dir = Path(__file__).parent
    assets_path = current_dir.parent / "assets" / "zone"
    output_file = assets_path / "province.json"
    province_list = ['서울특별시', '제주특별자치도', '전라남도', '전북특별자치도', '광주광역시', '경상남도', '경상북도', '울산광역시', '대구광역시', '부산광역시', '충청남도', '충청북도', '세종특별자치시', '대전광역시', '인천광역시']


    temp_dict = {}
    for province in province_list:
        if province == '서울특별시':
            temp_dict[province] = '서울'
        elif province == '제주특별자치도':
            temp_dict[province] = '제주'
        elif province == '전라남도':
            temp_dict[province] = '전남'
        elif province == '전북특별자치도':
            temp_dict[province] = '전북'
        elif province == '광주광역시':
            temp_dict[province] = '광주'
        elif province == '경상남도':
            temp_dict[province] = '경남'
        elif province == '경상북도':
            temp_dict[province] = '경북'
        elif province == '울산광역시':
            temp_dict[province] = '울산'
        elif province == '대구광역시':
            temp_dict[province] = '대구'
        elif province == '부산광역시':
            temp_dict[province] = '부산'
        elif province == '충청남도':
            temp_dict[province] = '충남'
        elif province == '충청북도':
            temp_dict[province] = '충북'
        elif province == '세종특별자치시':
            temp_dict[province] = '세종'
        elif province == '대전광역시':
            temp_dict[province] = '대전'
        elif province == '인천광역시':
            temp_dict[province] = '인천'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(temp_dict, f, ensure_ascii=False, indent=4)
    print(f"엑셀 파일을 JSON으로 변환하여 저장했습니다: {output_file}")

def convert_zone_excel_to_json():
    current_dir = Path(__file__).parent 
    assets_path = current_dir.parent / "assets" / "zone"
    
    excel_file = assets_path / "zone-tree.xlsx"
    province_file = assets_path / "province.json"
    output_file = assets_path / "zone.json"

    
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    with open(province_file, 'r', encoding='utf-8') as f:
        province_mapping = json.load(f)

    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(excel_file)
        
        desired_columns = ['행정구역코드', '1단계', '2단계', '격자 X', '격자 Y', '위도(초/100)', '경도(초/100)']

        df_selected = df[desired_columns]

        json_data = df_selected.to_dict('records')

        result = []
        temp_dict = {}
        for record in json_data:
            if record['행정구역코드']:
                temp_dict['region_code'] = record['행정구역코드']

            if record['1단계']:
                temp_dict['province'] = record['1단계']
                temp_dict['subregion'] = province_mapping.get(record['1단계'], 'null')

            if record['2단계']:
                temp_dict['region'] = str(record['2단계'])
                if record['2단계'] in northern_gyeonggi:
                    temp_dict['subregion'] = '경기북부'
                if record['2단계'] in southern_gyeonggi:
                    temp_dict['subregion'] = '경기남부'
                if record['2단계'] in western_gangwon:
                    temp_dict['subregion'] = '영서'
                if record['2단계'] in eastern_gangwon:
                    temp_dict['subregion'] = '영동'


            if record['격자 X']:
                temp_dict['nx'] = int(record['격자 X'])
            if record['격자 Y']:
                temp_dict['ny'] = int(record['격자 Y'])
            if record['위도(초/100)']:
                temp_dict['latitude'] = float(record['위도(초/100)'])
            if record['경도(초/100)']:
                temp_dict['longitude'] = float(record['경도(초/100)'])
            
            result.append(temp_dict.copy())

        # JSON 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"엑셀 파일을 JSON으로 변환하여 저장했습니다: {output_file}")
        
    except Exception as e:
        print(f"엑셀 파일 읽기 실패: {e}")
        return None
    
if __name__ == "__main__":
    # 도별 매핑 JSON 생성
    # make_provinces() 
    convert_zone_excel_to_json()