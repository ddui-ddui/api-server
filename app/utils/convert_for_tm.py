import math
from typing import Tuple
from pyproj import Transformer

def convert_wgs84_to_katec(lat: float, lon: float) -> Tuple[float, float]:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:5181", always_xy=True)
    tmX, tmY = transformer.transform(lon, lat)
    return tmX, tmY