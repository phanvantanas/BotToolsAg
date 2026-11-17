import pytest
from unittest.mock import patch
from src.services.power_service import power_service


def test_get_system_stats():
    """Kiểm tra lấy thông số phần cứng hệ thống."""
    stats = power_service.get_system_stats()
    assert "cpu_percent" in stats
    assert "ram_percent" in stats
    assert "ram_used_gb" in stats
    assert "disk_percent" in stats
    assert "uptime" in stats


@patch("subprocess.run")
def test_lock_workstation(mock_run):
    """Kiểm tra lệnh khóa màn hình gọi đúng tham số."""
    success, msg = power_service.lock_workstation()
    assert success is True
    assert "Đã khóa màn hình" in msg
    mock_run.assert_called_once_with(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)


@patch("subprocess.run")
def test_shutdown_system(mock_run):
    """Kiểm tra lệnh tắt máy gọi đúng tham số."""
    success, msg = power_service.shutdown_system(delay_seconds=15)
    assert success is True
    assert "15 giây" in msg
    mock_run.assert_called_once_with(
        ["shutdown.exe", "/s", "/t", "15", "/c", "Yeu cau tat may tu Telegram Bot"],
        check=True
    )


@patch("subprocess.run")
def test_abort_shutdown(mock_run):
    """Kiểm tra hủy lệnh tắt máy."""
    success, msg = power_service.abort_shutdown()
    assert success is True
    assert "Đã hủy lệnh" in msg
    mock_run.assert_called_once_with(["shutdown.exe", "/a"], check=True)
