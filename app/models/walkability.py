from enum import Enum

class DogSize(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"

class CoatType(str, Enum):
    single = "single"
    double = "double"

class CoatLength(str, Enum):
    short = "short"
    long = "long"

class AirQualityType(str, Enum):
    korean = "korean"
    who = "who"