from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from src.core.security import admin_only
from src.services.screen_service import screen_service
from src.core.logger import logger
from datetime import datetime


@admin_only
async def screen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /screen hoặc nút '📸 Chụp màn hình'."""
    chat_id = update.effective_chat.id
    await update.message.get_bot().send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

    try:
        # Chụp màn hình chính
        photo_buffer = screen_service.capture_screen(monitor_index=1)
        now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

        await update.message.reply_photo(
            photo=photo_buffer,
            caption=f"📸 **Ảnh chụp màn hình máy tính**\n🕒 Thời gian: `{now_str}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Lỗi khi gửi ảnh màn hình: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Không thể chụp ảnh màn hình: {str(e)}")
