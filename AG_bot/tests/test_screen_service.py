import pytest
import io
from PIL import Image
from src.services.screen_service import screen_service


def test_capture_screen():
    """Kiểm tra chụp màn hình trả về buffer ảnh JPEG hợp lệ."""
    buf = screen_service.capture_screen(monitor_index=1)
    assert isinstance(buf, io.BytesIO)
    assert buf.getbuffer().nbytes > 0

    # Kiểm tra ảnh mở được bằng PIL và có định dạng JPEG
    img = Image.open(buf)
    assert img.format == "JPEG"
    assert img.width > 0
    assert img.height > 0
