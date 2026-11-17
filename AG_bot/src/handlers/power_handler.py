from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.security import admin_only, verify_pin
from src.services.power_service import power_service
from src.core.logger import logger


@admin_only
async def lock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khóa màn hình máy tính."""
    success, msg = power_service.lock_workstation()
    await update.message.reply_text(msg)


@admin_only
async def shutdown_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý yêu cầu tắt máy kèm xác thực PIN."""
    user_id = update.effective_user.id

    # Kiểm tra xem người dùng có truyền mã PIN kèm theo không (/shutdown <PIN>)
    if context.args:
        pin = context.args[0].strip()
        ok, msg = verify_pin(user_id, pin)
        if not ok:
            await update.message.reply_text(f"🔒 {msg}")
            return

        success, result_msg = power_service.shutdown_system(delay_seconds=15)
        await update.message.reply_text(result_msg)
        return

    # Nếu chưa truyền PIN, hướng dẫn người dùng nhập đúng cú pháp
    await update.message.reply_text(
        "🔒 **YÊU CẦU MÃ PIN BẢO MẬT ĐỂ TẮT MÁY**\n\n"
        "Để tránh tắt nhầm hoặc bị tác động ngoài ý muốn, vui lòng gõ lệnh theo cú pháp:\n"
        "`/shutdown <mã_PIN_của_bạn>`\n\n"
        "*(Ví dụ: `/shutdown 1234`)*",
        parse_mode="Markdown"
    )


@admin_only
async def abort_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hủy lệnh tắt máy đang đếm ngược."""
    success, msg = power_service.abort_shutdown()
    await update.message.reply_text(msg)


@admin_only
async def power_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm xác nhận liên quan đến nguồn máy tính."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if data == "power:cancel":
        await query.edit_message_text("❌ Đã hủy thao tác.")
