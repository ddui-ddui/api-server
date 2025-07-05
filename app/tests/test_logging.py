import pytest
from app.config.logging_config import get_logger

# def test_logging_setup():
#     """로깅 설정이 정상적으로 작동하는지 테스트"""
#     logger = get_logger()
    
#     # 다양한 로그 레벨 테스트
#     logger.debug("Debug 메시지 테스트")
#     logger.info("Info 메시지 테스트")
#     logger.warning("Warning 메시지 테스트")
#     logger.error("Error 메시지 테스트")
    
#     # 테스트는 항상 통과 (로깅만 확인하는 용도)
#     assert True

# def test_context_vars_mock():
#     """컨텍스트 변수 모킹이 잘 되는지 테스트"""
#     from app.config.context import request_id, client_ip, user_agent
    
#     # 모킹된 값들이 정상적으로 반환되는지 확인
#     assert request_id.get() == "test-req-123"
#     assert client_ip.get() == "127.0.0.1"
#     assert user_agent.get() == "test-agent"
    
#     logger = get_logger()
#     logger.info("컨텍스트 변수 모킹 테스트 완료")

# @pytest.mark.unit
# def test_sensitive_data_masking():
#     """민감한 데이터 마스킹 테스트"""
#     from app.config.logging_config import mask_sensitive_data
    
#     # API 키 마스킹 테스트
#     test_message = "serviceKey=abcdefghijklmnopqrstuvwxyz1234567890"
#     masked = mask_sensitive_data(test_message)
    
#     logger = get_logger()
#     logger.info(f"원본: {test_message}")
#     logger.info(f"마스킹: {masked}")
    
#     # 마스킹이 적용되었는지 확인
#     assert "abcdefghijklmnopqrstuvwxyz1234567890" not in masked
#     assert "abcd" in masked  # 앞 4자리는 남아있어야 함