def convert_wgs84_to_tm(lat, lon):
    import math
    
    # GRS80 타원체
    RE = 6371.00877    # 지구 반경(km)
    GRID = 5.0         # 격자 간격(km)
    SLAT1 = 30.0       # 투영 위도1(degree)
    SLAT2 = 60.0       # 투영 위도2(degree)
    OLON = 126.0       # 기준점 경도(degree)
    OLAT = 38.0        # 기준점 위도(degree)
    XO = 43            # 기준점 X좌표(GRID)
    YO = 136           # 기준점 Y좌표(GRID)
    
    DEGRAD = math.pi / 180.0
    
    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD
    
    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)
    
    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    
    x = ra * math.sin(theta) + XO + 0.5
    y = ro - ra * math.cos(theta) + YO + 0.5
    
    # 환경공단 API용 TM 좌표로 변환 (정확한 상수값은 공식 문서 참조 필요)
    tmX = x * 1000  # 미터 단위로 변환
    tmY = y * 1000
    
    return tmX, tmY