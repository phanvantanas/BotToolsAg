import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.security import (
    is_user_authorized,
    verify_pin,
    admin_only,
    _FAILED_PIN_ATTEMPTS,
    _LOCKED_UNTIL,
)


def test_is_user_authorized():
    """Kiểm tra logic whitelist User ID."""
    assert is_user_authorized(999999999) is True
    assert is_user_authorized(12345) is False
    assert is_user_authorized(None) is False


def test_verify_pin():
    """Kiểm tra xác thực PIN và khóa sau 3 lần sai."""
    user_id = 999999999
    _FAILED_PIN_ATTEMPTS.clear()
    _LOCKED_UNTIL.clear()

    # Nhập đúng
    ok, msg = verify_pin(user_id, "1234")
    assert ok is True

    # Nhập sai lần 1
    ok, msg = verify_pin(user_id, "0000")
    assert ok is False
    assert "còn 2 lần thử" in msg

    # Nhập sai lần 2
    ok, msg = verify_pin(user_id, "1111")
    assert ok is False
    assert "còn 1 lần thử" in msg

    # Nhập sai lần 3 -> Khóa tài khoản
    ok, msg = verify_pin(user_id, "2222")
    assert ok is False
    assert "bị khóa" in msg

    # Thử lại khi đang bị khóa
    ok, msg = verify_pin(user_id, "1234")
    assert ok is False
    assert "thử lại sau" in msg


@pytest.mark.asyncio
async def test_admin_only_decorator():
    """Kiểm tra decorator admin_only chặn người lạ và cho phép admin."""
    mock_func = AsyncMock(return_value="executed")
    decorated_func = admin_only(mock_func)

    # Trường hợp 1: Người lạ (ID không nằm trong whitelist) -> Bị drop silently
    unauthorized_update = MagicMock()
    unauthorized_update.effective_user.id = 11111
    unauthorized_update.effective_user.username = "intruder"
    context = MagicMock()

    res = await decorated_func(unauthorized_update, context)
    assert res is None
    mock_func.assert_not_called()

    # Trường hợp 2: Admin hợp lệ -> Cho phép thực thi
    authorized_update = MagicMock()
    authorized_update.effective_user.id = 999999999
    authorized_update.effective_user.username = "owner"

    res = await decorated_func(authorized_update, context)
    assert res == "executed"
    mock_func.assert_called_once()
