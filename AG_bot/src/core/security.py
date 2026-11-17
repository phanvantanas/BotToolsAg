import time
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.config import settings
from src.core.logger import logger

# Bảng lưu vết thời gian request cuối để chống spam / flood
_LAST_REQUEST_TIME: dict[int, float] = {}
# Lưu số lần nhập sai PIN
_FAILED_PIN_ATTEMPTS: dict[int, int] = {}
# Thời gian bị khóa nếu sai PIN quá nhiều lần
_LOCKED_UNTIL: dict[int, float] = {}

MIN_REQUEST_INTERVAL_SECONDS = 0.5
MAX_PIN_ATTEMPTS = 3
LOCKOUT_DURATION_SECONDS = 300  # Khóa 5 phút nếu sai 3 lần


def is_user_authorized(user_id: int | None) -> bool:
    """Kiểm tra Telegram user_id có nằm trong danh sách được phép không."""
    if not user_id:
        return False
    return user_id in settings.ALLOWED_USER_IDS


def is_user_locked(user_id: int) -> bool:
    """Kiểm tra user có đang bị tạm khóa do nhập sai PIN không."""
    locked_time = _LOCKED_UNTIL.get(user_id, 0)
    if time.time() < locked_time:
        return True
    return False


def verify_pin(user_id: int, input_pin: str) -> tuple[bool, str]:
    """
    Xác thực mã PIN bảo mật cho các tác vụ nhạy cảm (Tắt máy, Khởi động lại).
    Trả về (thành công, thông báo lỗi).
    """
    if is_user_locked(user_id):
        remaining = int(_LOCKED_UNTIL[user_id] - time.time())
        return False, f"Bạn đã nhập sai PIN quá nhiều lần. Vui lòng thử lại sau {remaining} giây."

    clean_pin = input_pin.strip()
    if clean_pin == settings.SECURITY_PIN:
        _FAILED_PIN_ATTEMPTS[user_id] = 0
        return True, "Xác thực mã PIN thành công."

    # Xử lý nhập sai
    attempts = _FAILED_PIN_ATTEMPTS.get(user_id, 0) + 1
    _FAILED_PIN_ATTEMPTS[user_id] = attempts
    logger.warning(f"Người dùng {user_id} nhập sai mã PIN (Lần {attempts}/{MAX_PIN_ATTEMPTS}).")

    if attempts >= MAX_PIN_ATTEMPTS:
        _LOCKED_UNTIL[user_id] = time.time() + LOCKOUT_DURATION_SECONDS
        _FAILED_PIN_ATTEMPTS[user_id] = 0
        return False, f"Nhập sai PIN 3 lần! Tài khoản tạm thời bị khóa lệnh nhạy cảm trong 5 phút."

    remaining_attempts = MAX_PIN_ATTEMPTS - attempts
    return False, f"Mã PIN không chính xác! Bạn còn {remaining_attempts} lần thử."


def admin_only(func):
    """
    Decorator bảo vệ handler Telegram:
    - Nếu không thuộc Whitelist: Drop silently (không phản hồi, ghi log bảo mật).
    - Nếu thuộc Whitelist: Cho phép thực thi ngay lập tức.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id if user else None
        username = user.username if user else "Unknown"

        if not is_user_authorized(user_id):
            logger.warning(
                f"[BẢO MẬT] Từ chối truy cập từ người lạ: ID={user_id}, Username=@{username}"
            )
            # Không trả lời người lạ để tránh lộ sự tồn tại của bot
            return

        text = update.message.text if update.message and update.message.text else ""
        if text:
            logger.info(f"Đã xác thực User ID={user_id} (@{username}) thực hiện: {text[:60]}")

        return await func(update, context, *args, **kwargs)

    return wrapper
