import pytest
from unittest.mock import patch, AsyncMock
from src.services.agy_service import agy_service


def test_model_switching():
    """Kiểm tra thay đổi model."""
    assert agy_service.set_model("claude-sonnet-4-6") is True
    assert agy_service.current_model == "claude-sonnet-4-6"

    # Model không tồn tại
    assert agy_service.set_model("non-existent-model") is False
    assert agy_service.current_model == "claude-sonnet-4-6"


def test_session_reset():
    """Kiểm tra reset session sang phiên mới."""
    agy_service.continue_session = True
    agy_service.reset_session()
    assert agy_service.continue_session is False


def test_working_dir_switching():
    """Kiểm tra xem và đổi thư mục làm việc."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        success, msg = agy_service.set_working_dir(tmpdir)
        assert success is True
        assert agy_service.get_working_dir().lower() == tmpdir.lower()
        # Đổi thư mục phải tự động reset session
        assert agy_service.continue_session is False

    # Thư mục không tồn tại
    success, msg = agy_service.set_working_dir("E:\\path_does_not_exist_123456")
    assert success is False
    assert "không tồn tại" in msg


@pytest.mark.asyncio
async def test_execute_prompt():
    """Kiểm tra gọi execute_prompt với mock subprocess."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Ket qua tu Antigravity", b"")
    mock_process.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        agy_service.continue_session = True
        agy_service.current_model = "gemini-3.8-flash-high"

        result = await agy_service.execute_prompt("test question")
        assert result == "Ket qua tu Antigravity"
        mock_exec.assert_called_once()


def test_parse_reset_time():
    """Kiểm tra trích xuất thời gian reset từ thông báo lỗi quota."""
    # Định dạng đầy đủ
    err_text = "error: Individual quota reached. Resets in 162h14m5s."
    assert agy_service._parse_reset_time(err_text) == "162h 14m 5s"

    # Chỉ có giờ và phút
    err_text2 = "Quota exceeded! Resets in 5h30m"
    assert agy_service._parse_reset_time(err_text2) == "5h 30m"

    # Không có thông tin reset
    assert agy_service._parse_reset_time("Syntax error in command") is None


@pytest.mark.asyncio
async def test_execute_prompt_quota_error():
    """Kiểm tra xử lý lỗi quota và tự động ghi nhớ vào cache."""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (
        b"",
        b"error: Individual quota reached. Resets in 12h30m0s.\nAGY_ERROR: {\"error_code\": 429}"
    )
    mock_process.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_process):
        agy_service.current_model = "gemini-3.8-flash-high"
        result = await agy_service.execute_prompt("test prompt")
        assert "Hạn mức (Quota)" in result
        assert "12h 30m 0s" in result
        # Cache quota phải được cập nhật
        assert "gemini-3.8-flash-high" in agy_service._quota_cache
        assert agy_service._quota_cache["gemini-3.8-flash-high"]["available"] is False
