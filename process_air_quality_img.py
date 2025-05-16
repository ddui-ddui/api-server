import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# 이미지 다운로드 함수
def get_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return np.array(img)
    except Exception as e:
        print(f"이미지 다운로드 오류: {e}")
        return None

# 오른쪽의 색상 스케일 추출
def extract_color_scale(image, map_boundaries):
    height, width = image.shape[:2]
    scale_x_start = map_boundaries['right']
    color_scale = image[:, scale_x_start:].copy()
    return color_scale

# 검정색과 회색을 감지하되 빨간색 영역은 보존하는 마스크 생성
def create_boundary_mask(map_region):
    # HSV 색상 공간으로 변환
    hsv = cv2.cvtColor(map_region, cv2.COLOR_RGB2HSV)
    
    # 1. 검정색 범위 정의 (좀 더 제한적으로)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 100, 60])  # 명도를 낮춰 진한 검정색만 포함
    black_mask = cv2.inRange(hsv, lower_black, upper_black)
    
    # 2. 회색 범위 정의 (좀 더 제한적으로)
    lower_gray = np.array([0, 0, 120])
    upper_gray = np.array([180, 60, 210])  # 채도를 낮춰 회색만 포함
    gray_mask = cv2.inRange(hsv, lower_gray, upper_gray)
    
    # 3. 파란빛 회색 범위 (경계선)
    lower_blue_gray = np.array([90, 10, 130])
    upper_blue_gray = np.array([150, 70, 210])
    blue_gray_mask = cv2.inRange(hsv, lower_blue_gray, upper_blue_gray)
    
    # 4. 짙은 청색 범위 (화살표)
    lower_dark_blue = np.array([100, 30, 10])
    upper_dark_blue = np.array([130, 255, 90])
    dark_blue_mask = cv2.inRange(hsv, lower_dark_blue, upper_dark_blue)
    
    # 5. 더 넓은 짙은 청색 범위 (추가 화살표)
    lower_dark_blue2 = np.array([90, 20, 10])
    upper_dark_blue2 = np.array([150, 255, 120])
    dark_blue_mask2 = cv2.inRange(hsv, lower_dark_blue2, upper_dark_blue2)
    
    # 6. 녹색 영역의 화살표
    lower_green_arrow = np.array([80, 30, 70])
    upper_green_arrow = np.array([100, 255, 180])
    green_arrow_mask = cv2.inRange(hsv, lower_green_arrow, upper_green_arrow)
    
    # 7. 흰색 화살표 (녹색 영역에서)
    lower_white_arrow = np.array([0, 0, 200])
    upper_white_arrow = np.array([180, 50, 255])
    white_arrow_mask = cv2.inRange(hsv, lower_white_arrow, upper_white_arrow)
    
    # 모든 마스크 결합
    combined_mask = cv2.bitwise_or(
        black_mask, 
        cv2.bitwise_or(
            gray_mask, 
            cv2.bitwise_or(
                blue_gray_mask,
                cv2.bitwise_or(
                    dark_blue_mask, 
                    cv2.bitwise_or(
                        dark_blue_mask2,
                        cv2.bitwise_or(green_arrow_mask, white_arrow_mask)
                    )
                )
            )
        )
    )
    
    # 8. 빨간색 영역 보존 (인페인팅 마스크에서 제외)
    # 빨간색 HSV 범위 (빨간색은 HSV에서 0도 또는 180도 근처)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    
    # 두 빨간색 범위 합치기
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    
    # 빨간색 영역은 마스크에서 제외
    combined_mask = cv2.bitwise_and(combined_mask, cv2.bitwise_not(red_mask))
    
    # 에지 검출 (선형 요소 강화)
    edges = cv2.Canny(map_region, 50, 150)
    
    # 에지도 빨간색 영역은 제외
    edges = cv2.bitwise_and(edges, cv2.bitwise_not(red_mask))
    
    # 에지와 마스크 결합
    combined_mask = cv2.bitwise_or(combined_mask, edges)
    
    # 모폴로지 연산으로 마스크 확장 (적당히)
    kernel = np.ones((3, 3), np.uint8)
    combined_mask = cv2.dilate(combined_mask, kernel, iterations=1)  # 반복 횟수 1로 제한
    
    return combined_mask

# 인페인팅을 사용하여 경계선 및 화살표 제거
def remove_boundaries_with_inpainting(image, map_boundaries):
    # 이미지 복사
    result = image.copy()
    height, width = image.shape[:2]
    
    # 맵 영역 추출 (상하좌우 경계 사용)
    top = map_boundaries['top']
    bottom = map_boundaries['bottom']
    left = map_boundaries['left']
    right = map_boundaries['right']
    
    # 맵 영역과 범례 영역 구분
    map_region = result[top:bottom, left:right].copy()
    
    # 경계선 마스크 생성
    boundary_mask = create_boundary_mask(map_region)
    
    # 마스크 저장 (디버깅용)
    # cv2.imwrite("inpaint_mask.png", boundary_mask)
    
    # 인페인팅 적용
    inpainted_map = cv2.inpaint(map_region, boundary_mask, 7, cv2.INPAINT_TELEA)
    
    # 결과 이미지에 처리된 맵 영역 삽입
    result[top:bottom, left:right] = inpainted_map
    
    return result

# 맵 영역 미리보기 함수
# def preview_map_region(image, map_boundaries):
#     result = image.copy()
    
#     # 맵 영역 경계 그리기
#     top = map_boundaries['top']
#     bottom = map_boundaries['bottom']
#     left = map_boundaries['left']
#     right = map_boundaries['right']
    
#     # 빨간색 사각형으로 경계 표시
#     cv2.rectangle(result, (left, top), (right, bottom), (255, 0, 0), 2)
    
#     # 미리보기 저장
#     cv2.imwrite("map_region_preview.png", cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
    
#     # 미리보기 표시
#     plt.figure(figsize=(12, 8))
#     plt.imshow(result)
#     plt.title("맵 영역 미리보기 (파란색 테두리)")
#     plt.savefig("map_boundaries_preview.png")
#     plt.close()
    
#     print("맵 영역 미리보기가 'map_boundaries_preview.png'에 저장되었습니다.")

# 메인 함수
def process_pm25_map(url, map_boundaries, debug=False):
    image = get_image(url)
    if image is None:
        return None
    
    # 디버그 모드에서 맵 영역 미리보기
    # if debug:
    #     preview_map_region(image, map_boundaries)
    
    processed_image = remove_boundaries_with_inpainting(image, map_boundaries)
    
    # 최종 결과물 저장
    cv2.imwrite("processed_pm25_map.png", cv2.cvtColor(processed_image, cv2.COLOR_RGB2BGR))
    
    # 디버깅 모드일 경우 비교 이미지 생성
    # if debug:
    #     plt.figure(figsize=(15, 10))
    #     plt.subplot(1, 3, 1)
    #     plt.title("원본 이미지")
    #     plt.imshow(image)
        
    #     plt.subplot(1, 3, 2)
    #     plt.title("인페인팅 마스크")
    #     mask = cv2.imread("inpaint_mask.png", cv2.IMREAD_GRAYSCALE)
    #     plt.imshow(mask, cmap='gray')
        
    #     plt.subplot(1, 3, 3)
    #     plt.title("처리된 이미지")
    #     plt.imshow(processed_image)
        
    #     plt.savefig("debug_comparison.png")
    
    print("처리 완료. 이미지가 'processed_pm25_map.png'로 저장되었습니다.")
    return processed_image

url = "https://www.airkorea.or.kr/file/proxyImage?fileName=2025/05/13/23/09km/AQF.20250513.NIER_09_01.PM10.1hsp.2025051321.png"
image = get_image(url)

if image is not None:
    height, width = image.shape[:2]
    
    # 맵 영역 경계 설정 - 이 값들을 조정하세요
    map_boundaries = {
        'top': int(height * 0.08),
        'bottom': int(height * 0.988), 
        'left': int(width * 0.015),
        'right': int(width * 0.89)
    }
    
    # 맵 영역 테스트 (미리보기 생성)
    # preview_map_region(image, map_boundaries)
    
    # 실제 처리 실행
    processed_image = process_pm25_map(url, map_boundaries, debug=False)
else:
    print("이미지를 불러올 수 없습니다.")