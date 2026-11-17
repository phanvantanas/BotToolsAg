import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm và nạp file .env từ thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Quản lý các biến môi trường và thiết lập an toàn cho AG-Telebot."""

    def __init__(self):
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        
        # Xử lý danh sách User ID được cấp phép
        raw_ids = os.getenv("ALLOWED_USER_IDS", "").strip()
        self.ALLOWED_USER_IDS: set[int] = set()
        if raw_ids:
            for item in raw_ids.split(","):
                item = item.strip()
                if item.isdigit():
                    self.ALLOWED_USER_IDS.add(int(item))

        # Mã PIN bảo mật
        self.SECURITY_PIN: str = os.getenv("SECURITY_PIN", "1234").strip()

        # Model mặc định
        self.DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash-high").strip()

        # Đường dẫn agy.exe mặc định theo thư mục người dùng hiện tại
        default_agy = str(Path.home() / ".gemini" / "bin" / "agy.exe")
        self.AGY_PATH: str = os.getenv("AGY_PATH", default_agy).strip()

        # Thời gian chờ tối đa khi chạy Antigravity (giây)
        self.AGY_TIMEOUT: int = int(os.getenv("AGY_TIMEOUT", "180"))

        # Giới hạn kích thước ảnh chụp màn hình gửi qua Telegram (pixel)
        self.SCREENSHOT_MAX_WIDTH: int = 1920

        # Thư mục lưu trữ tạm
        self.TEMP_DIR: Path = BASE_DIR / "temp"
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        """Kiểm tra tính hợp lệ của cấu hình tối thiểu trước khi khởi động bot."""
        if not self.TELEGRAM_BOT_TOKEN or self.TELEGRAM_BOT_TOKEN == "your_bot_token_here":
            raise ValueError(
                "LỖI CẤU HÌNH: TELEGRAM_BOT_TOKEN chưa được thiết lập trong file .env!\n"
                "Vui lòng điền Bot Token lấy từ @BotFather."
            )
        if not self.ALLOWED_USER_IDS:
            raise ValueError(
                "LỖI BẢO MẬT: ALLOWED_USER_IDS chưa được thiết lập trong file .env!\n"
                "Cần ít nhất một Telegram User ID của bạn (lấy từ @userinfobot) để tránh bot bị truy cập trái phép."
            )


settings = Settings()
