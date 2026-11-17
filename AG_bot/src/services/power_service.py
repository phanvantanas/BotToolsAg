import subprocess
import time
import psutil
from datetime import datetime
from src.core.logger import logger


class PowerService:
    """Dịch vụ quản lý nguồn và theo dõi thông số hệ thống Windows."""

    @staticmethod
    def get_system_stats() -> dict:
        """Thu thập thông số tài nguyên phần cứng máy tính."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            uptime_seconds = int(time.time() - psutil.boot_time())
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"

            return {
                "cpu_percent": cpu_percent,
                "ram_percent": ram.percent,
                "ram_used_gb": round(ram.used / (1024 ** 3), 2),
                "ram_total_gb": round(ram.total / (1024 ** 3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024 ** 3), 2),
                "boot_time": boot_time,
                "uptime": uptime_str,
            }
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông số hệ thống: {e}", exc_info=True)
            return {}

    @staticmethod
    def lock_workstation() -> tuple[bool, str]:
        """Khóa màn hình máy tính Windows ngay lập tức."""
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return True, "🔒 Đã khóa màn hình máy tính thành công!"
        except Exception as e:
            logger.error(f"Lỗi khi khóa màn hình: {e}")
            return False, f"❌ Không thể khóa màn hình: {e}"

    @staticmethod
    def shutdown_system(delay_seconds: int = 15) -> tuple[bool, str]:
        """Tắt máy tính (có đếm ngược delay_seconds để kịp hủy nếu bấm nhầm)."""
        try:
            cmd = ["shutdown.exe", "/s", "/t", str(delay_seconds), "/c", "Yeu cau tat may tu Telegram Bot"]
            subprocess.run(cmd, check=True)
            return True, f"⛔ Máy tính sẽ tắt sau {delay_seconds} giây! (Dùng lệnh /abort nếu muốn hủy)."
        except Exception as e:
            logger.error(f"Lỗi khi tắt máy: {e}")
            return False, f"❌ Lỗi khi thực hiện lệnh tắt máy: {e}"

    @staticmethod
    def abort_shutdown() -> tuple[bool, str]:
        """Hủy lệnh tắt máy đang đếm ngược."""
        try:
            subprocess.run(["shutdown.exe", "/a"], check=True)
            return True, "✅ Đã hủy lệnh tắt máy tính thành công!"
        except Exception as e:
            return False, f"⚠️ Không có lệnh tắt máy nào đang chờ hủy hoặc xảy ra lỗi: {e}"


power_service = PowerService()
