import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat, Message, CallbackQuery
from telegram.ext import ContextTypes
from src.config import settings
from src.services.agy_service import agy_service, AVAILABLE_MODELS
from src.handlers.agy_handler import (
    new_session_handler,
    model_menu_handler,
    model_callback_handler,
    folder_command_handler,
)
from src.handlers.command_handler import status_handler


def create_mock_update(user_id: int, text: str = ""):
    """Tạo đối tượng Mock Update hợp lệ với người dùng trong whitelist."""
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = user_id
    user.username = "test_admin"
    user.first_name = "Admin"

    chat = MagicMock(spec=Chat)
    chat.id = user_id

    message = MagicMock(spec=Message)
    message.text = text
    message.reply_text = AsyncMock()
    message.get_bot = MagicMock()
    bot = MagicMock()
    bot.send_chat_action = AsyncMock()
    message.get_bot.return_value = bot

    update.effective_user = user
    update.effective_chat = chat
    update.message = message
    return update


@pytest.fixture
def admin_user_id():
    """Lấy User ID hợp lệ đầu tiên từ cấu hình."""
    return next(iter(settings.ALLOWED_USER_IDS))


@pytest.mark.asyncio
async def test_feature_new_session(admin_user_id):
    """1. Test tính năng 'Phiên mới' (/new): Đặt lại trạng thái tiếp tục hội thoại."""
    update = create_mock_update(admin_user_id, "/new")
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    agy_service.continue_session = True
    await new_session_handler(update, context)

    # Đảm bảo cờ continue_session đã chuyển sang False
    assert agy_service.continue_session is False
    # Kiểm tra phản hồi gửi tới người dùng
    update.message.reply_text.assert_called_once()
    reply_msg = update.message.reply_text.call_args[0][0]
    assert "Đã tạo phiên hội thoại mới" in reply_msg


@pytest.mark.asyncio
async def test_feature_status(admin_user_id):
    """2. Test tính năng 'Trạng thái' (/status): Báo cáo phần cứng và Antigravity."""
    update = create_mock_update(admin_user_id, "/status")
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    await status_handler(update, context)

    update.message.reply_text.assert_called_once()
    reply_msg = update.message.reply_text.call_args[0][0]
    # Kiểm tra các thông số bắt buộc
    assert "BÁO CÁO TRẠNG THÁI HỆ THỐNG" in reply_msg
    assert "CPU:" in reply_msg
    assert "RAM:" in reply_msg
    assert "Ổ đĩa C:" in reply_msg
    assert "Model đang dùng:" in reply_msg
    assert "Thư mục:" in reply_msg


@pytest.mark.asyncio
async def test_feature_model_and_quota(admin_user_id):
    """3. Test tính năng 'Đổi Model' (/model) và Callback chuyển model."""
    update = create_mock_update(admin_user_id, "/model")
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # Giả lập cache quota có sẵn để phản hồi ngay
    agy_service._quota_cache = {
        "gemini-3.8-flash-high": {"available": True, "resets_in": None, "error": None},
        "claude-sonnet-4-6": {"available": False, "resets_in": "10h 15m", "error": "Hết quota"},
    }
    agy_service._quota_cache_time = 9999999999.0  # Còn hạn vĩnh viễn trong test

    # 3.1. Mở menu model
    await model_menu_handler(update, context)
    update.message.reply_text.assert_called_once()
    menu_text = update.message.reply_text.call_args[0][0]
    reply_markup = update.message.reply_text.call_args[1]["reply_markup"]

    assert "Cài đặt Model AI" in menu_text
    assert reply_markup is not None
    # Kiểm tra danh sách nút
    button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
    assert any("Kiểm tra / Làm mới Quota" in t for t in button_texts)
    assert any("Claude Sonnet 4.6 (10h 15m)" in t for t in button_texts)

    # 3.2. Test callback chuyển đổi sang Claude Sonnet
    cb_update = MagicMock(spec=Update)
    cb_user = MagicMock(spec=User)
    cb_user.id = admin_user_id
    cb_update.effective_user = cb_user
    cb_update.message = None

    query = MagicMock(spec=CallbackQuery)
    query.data = "set_model:claude-sonnet-4-6"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    cb_update.callback_query = query

    await model_callback_handler(cb_update, context)

    # Xác nhận model đã được cập nhật
    assert agy_service.current_model == "claude-sonnet-4-6"
    query.edit_message_text.assert_called_once()
    edit_text = query.edit_message_text.call_args[0][0]
    assert "Đã chuyển sang:" in edit_text
    assert "Claude Sonnet 4.6" in edit_text

    # Đổi lại model mặc định ban đầu
    agy_service.set_model("gemini-3.8-flash-high")


@pytest.mark.asyncio
async def test_feature_folder_management(admin_user_id):
    """4. Test tính năng 'Thư mục' (/cd, /folder): Xem và đổi thư mục làm việc."""
    update = create_mock_update(admin_user_id, "/cd")
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # 4.1. Xem thư mục hiện tại (không có đối số)
    context.args = []
    await folder_command_handler(update, context)
    update.message.reply_text.assert_called_once()
    msg = update.message.reply_text.call_args[0][0]
    assert "Thư mục làm việc hiện tại:" in msg

    # 4.2. Đổi sang thư mục hợp lệ
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        context.args = [tmp_dir]
        update.message.reply_text.reset_mock()
        await folder_command_handler(update, context)
        update.message.reply_text.assert_called_once()
        success_msg = update.message.reply_text.call_args[0][0]
        assert "Đã chuyển thư mục làm việc thành công" in success_msg
        assert agy_service.get_working_dir().lower() == tmp_dir.lower()
        # Chuyển thư mục phải tự động reset session
        assert agy_service.continue_session is False

    # 4.3. Đổi sang thư mục không tồn tại
    context.args = ["E:\\duong_dan_khong_ton_tai_xyz_999"]
    update.message.reply_text.reset_mock()
    await folder_command_handler(update, context)
    update.message.reply_text.assert_called_once()
    err_msg = update.message.reply_text.call_args[0][0]
    assert "Thư mục không tồn tại" in err_msg


@pytest.mark.asyncio
async def test_feature_view_logs(admin_user_id):
    """5. Test tính năng xem log từ xa qua Telegram (/log)."""
    from src.handlers.command_handler import log_handler

    update = create_mock_update(admin_user_id, "/log")
    update.message.reply_document = AsyncMock()
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # 5.1. Xem log mặc định (dạng text tóm tắt)
    context.args = []
    await log_handler(update, context)
    update.message.reply_text.assert_called_once()
    log_reply = update.message.reply_text.call_args[0][0]
    assert "DÒNG LOG MỚI NHẤT" in log_reply

    # 5.2. Yêu cầu tải file đính kèm (/log file)
    context.args = ["file"]
    update.message.reply_text.reset_mock()
    await log_handler(update, context)
    update.message.reply_document.assert_called_once()
    caption = update.message.reply_document.call_args[1].get("caption", "")
    assert "Toàn bộ file nhật ký" in caption


@pytest.mark.asyncio
async def test_feature_log_keyboard_and_shortcut(admin_user_id):
    """6. Test phím tắt '📜 Xem Log' trên bàn phím và điều hướng tin nhắn text."""
    from src.handlers.command_handler import get_main_keyboard
    from src.handlers.agy_handler import message_handler

    # 6.1. Kiểm tra nút bấm trên Reply Keyboard
    kb = get_main_keyboard()
    button_labels = [btn.text for row in kb.keyboard for btn in row]
    assert "📜 Xem Log" in button_labels

    # 6.2. Nhấn nút '📜 Xem Log' gửi vào message_handler
    update = create_mock_update(admin_user_id, "📜 Xem Log")
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    await message_handler(update, context)
    update.message.reply_text.assert_called_once()
    reply_msg = update.message.reply_text.call_args[0][0]
    assert "DÒNG LOG MỚI NHẤT" in reply_msg


@pytest.mark.asyncio
async def test_bot_commands_and_suggestions():
    """7. Test danh sách BotCommand để hiện gợi ý tự động khi gõ / trên Telegram."""
    from src.main import BOT_COMMANDS, post_init
    cmd_dict = {cmd.command: cmd.description for cmd in BOT_COMMANDS}

    # Đảm bảo các lệnh cốt lõi đều có trong danh sách gợi ý kèm mô tả
    assert "cd" in cmd_dict
    assert "log" in cmd_dict
    assert "start" in cmd_dict
    assert "status" in cmd_dict
    assert "model" in cmd_dict
    assert "new" in cmd_dict
    assert "screen" in cmd_dict
    assert "lock" in cmd_dict
    assert "shutdown" in cmd_dict
    assert "abort" in cmd_dict

    # Test hàm post_init gọi set_my_commands
    mock_app = MagicMock()
    mock_app.bot.set_my_commands = AsyncMock()
    await post_init(mock_app)
    mock_app.bot.set_my_commands.assert_called_once_with(BOT_COMMANDS)


