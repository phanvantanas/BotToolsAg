import pytest
import os
from src.config import settings

@pytest.fixture(autouse=True)
def setup_test_env():
    """Thiết lập môi trường an toàn khi chạy tests."""
    original_allowed = settings.ALLOWED_USER_IDS.copy()
    original_pin = settings.SECURITY_PIN
    
    settings.ALLOWED_USER_IDS = {999999999}
    settings.SECURITY_PIN = "1234"
    
    yield
    
    settings.ALLOWED_USER_IDS = original_allowed
    settings.SECURITY_PIN = original_pin
