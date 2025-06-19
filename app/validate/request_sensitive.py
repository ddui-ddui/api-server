from fastapi import HTTPException
from app.models.response import error_response


ALLOWED_SENSITIVITIES = {
    "puppy", "senior", "heart_disease", "respiratory", "obesity", "brachycephalic"
}

def validate_sensitivities(sensitivities: str) -> str:
    """민감군 목록 검증"""
    if not sensitivities:
        return sensitivities
    
    sensitivity_list = [s.strip() for s in sensitivities.split(",")]
    invalid_sensitivities = set(sensitivity_list) - ALLOWED_SENSITIVITIES
    
    if invalid_sensitivities:
        raise error_response(422, f"허용되지 않는 민감군: {', '.join(invalid_sensitivities)}, 허용되는 값: {', '.join(ALLOWED_SENSITIVITIES)}")
    
    return sensitivities