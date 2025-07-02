from unittest.mock import MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

base_parameter_data = {
    "lat": 37.5665,
    "lon": 126.9780,
    "dog_size": "medium",
    "sensitivities": "puppy",
    "air_quality_type": "who",
    "coat_type": "double",
    "coat_length": "long"
}

@pytest.mark.api
def test_walkability_current_success(client):
    """Current API 성공 응답 테스트"""        
    response = client.get("/api/v1/walkability/current", params={**base_parameter_data})
    assert response.status_code == 200