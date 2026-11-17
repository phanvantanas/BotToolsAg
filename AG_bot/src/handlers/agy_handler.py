import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from src.core.security import admin_only
from src.services.agy_service import agy_service, AVAILABLE_MODELS
from src.core.logger import logger

MAX_TELEGRAM_MESSAGE_LENGTH = 4000


def get_model_selection_keyboard(quota_results: dict | None = None) -> InlineKeyboardMarkup:
    """
    Tạo Inline Keyboard danh sách model AI.
    Nếu có quota_results, hiển thị 🟢/🔴 kèm thời gian reset ngay trên nút.
    """
    buttons = []
    current_key = agy_service.current_model

    for key, name in AVAILABLE_MODELS.items():
        # Tiền tố model đang dùng
        active_mark = "✅ " if key == current_key else ""

        if quota_results is not None:
            info = quota_results.get(key, {})
            if info.get("available", True):
                status = "🟢 "
            else:
                resets_in = info.get("resets_in")
                status = "🔴 "
                # Rút gọn bớt chữ "(Thinking)" để nút hiển thị vừa vặn trên điện thoại
                clean_name = name.replace(" (Thinking)", "")
                name = f"{clean_name} ({resets_in})" if resets_in else f"{clean_name} (hết quota)"
        else:
            status = ""

        label = f"{active_mark}{status}{name}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"set_model:{key}")])

    # Nút bấm làm mới trạng thái Quota trực tiếp
    buttons.append([InlineKeyboardButton("🔄 Kiểm tra / Làm mới Quota", callback_data="refresh_quota")])

    return InlineKeyboardMarkup(buttons)


def _build_model_menu_text(quota_results: dict | None = None) -> str:
    """Tạo nội dung tin nhắn cho menu chọn model."""
    current_name = AVAILABLE_MODELS.get(agy_service.current_model, agy_service.current_model)

    if quota_results is None:
        return (
            f"⚙️ **Cài đặt Model AI**\n\n"
            f"Model hiện tại: `{current_name}`\n"
            f"Chọn một model bên dưới để chuyển đổi:"
        )

    available_count = sum(1 for v in quota_results.values() if v.get("available", False))
    total = len(AVAILABLE_MODELS)
    quota_summary = f"🟢 **{available_count}/{total}** model còn quota"

    return (
        f"⚙️ **Cài đặt Model AI**\n\n"
        f"Model hiện tại: `{current_name}`\n"
        f"Trạng thái: {quota_summary}\n\n"
        f"🟢 = Còn quota | 🔴 = Hết quota (kèm thời gian reset)\n"
        f"Bấm model bên dưới để chuyển đổi:"
    )


@admin_only
async def new_session_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /new hoặc nút '✨ Phiên mới'."""
    agy_service.reset_session()
    await update.message.reply_text(
        "✨ **Đã tạo phiên hội thoại mới thành công!**\n"
        "Ngữ cảnh cũ đã được đặt lại. Câu hỏi hoặc tác vụ tiếp theo của bạn sẽ là một phiên độc lập mới hoàn toàn.",
        parse_mode="Markdown"
    )


@admin_only
async def model_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị menu chọn model AI, tích hợp kiểm tra quota song song."""
    import time
    now = time.time()
    # Nếu đã có cache còn hạn thì hiển thị ngay không phải chờ
    has_valid_cache = bool(
        agy_service._quota_cache and (now - agy_service._quota_cache_time < agy_service._quota_cache_ttl)
    )

    if not has_valid_cache:
        loading_msg = await update.message.reply_text(
            "⚙️ **Đổi Model AI**\n"
            "🔍 _Đang kiểm tra quota từng model..._",
            parse_mode="Markdown"
        )
        await update.message.get_bot().send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        quota_results = await agy_service.check_all_models_quota()
        try:
            await loading_msg.delete()
        except Exception:
            pass
    else:
        quota_results = agy_service._quota_cache

    await update.message.reply_text(
        _build_model_menu_text(quota_results),
        reply_markup=get_model_selection_keyboard(quota_results),
        parse_mode="Markdown"
    )


@admin_only
async def model_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi người dùng bấm chọn model hoặc làm mới quota trong Inline Keyboard."""
    query = update.callback_query
    data = query.data or ""

    if data.startswith("set_model:"):
        await query.answer()
        model_key = data.split(":", 1)[1]
        success = agy_service.set_model(model_key)
        if not success:
            return

        model_name = AVAILABLE_MODELS.get(model_key, model_key)
        quota_results = agy_service._quota_cache or None
        new_keyboard = get_model_selection_keyboard(quota_results)

        # Cập nhật tin nhắn với dấu tích ✅ chuyển sang model mới
        await query.edit_message_text(
            f"✅ **Đã chuyển sang:** `{model_name}`\n\n"
            f"{_build_model_menu_text(quota_results)}",
            reply_markup=new_keyboard,
            parse_mode="Markdown"
        )

    elif data == "refresh_quota":
        await query.answer("🔍 Đang kiểm tra lại quota tất cả model...")
        await query.edit_message_text(
            "⚙️ **Cài đặt Model AI**\n\n"
            "⏳ _Đang kiểm tra lại trạng thái quota tất cả model, vui lòng chờ giây lát..._",
            parse_mode="Markdown"
        )
        quota_results = await agy_service.check_all_models_quota(force_refresh=True)
        await query.edit_message_text(
            _build_model_menu_text(quota_results),
            reply_markup=get_model_selection_keyboard(quota_results),
            parse_mode="Markdown"
        )


async def send_response_message(update: Update, text: str) -> None:
    """Gửi phản hồi về Telegram, tự động chia nhỏ hoặc gửi file nếu quá dài."""
    if len(text) <= MAX_TELEGRAM_MESSAGE_LENGTH:
        try:
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(text)
    else:
        preview_text = text[:1500] + "\n\n...(Nội dung quá dài, toàn bộ kết quả được đính kèm trong tệp bên dưới)..."
        try:
            await update.message.reply_text(preview_text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(preview_text)

        file_bytes = io.BytesIO(text.encode("utf-8"))
        file_bytes.name = "antigravity_response.txt"
        await update.message.reply_document(
            document=file_bytes,
            caption="📄 Toàn bộ kết quả trả về từ Antigravity."
        )


@admin_only
async def folder_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /cd hoặc /folder để xem hoặc đổi thư mục làm việc."""
    if not context.args:
        current_dir = agy_service.get_working_dir()
        msg = (
            f"📂 **Thư mục làm việc hiện tại:**\n"
            f"`{current_dir}`\n\n"
            f"💡 **Cách đổi thư mục:**\n"
            f"Gõ `/cd <đường_dẫn>` hoặc `/folder <đường_dẫn>`\n\n"
            f"*(Ví dụ: `/cd e:\\tool\\AG` hoặc `/cd C:\\Users\\Bao\\Desktop`)*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    target_dir = " ".join(context.args).strip()
    success, msg = agy_service.set_working_dir(target_dir)
    await update.message.reply_text(msg, parse_mode="Markdown")


@admin_only
async def ask_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /ask <prompt>."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Vui lòng nhập nội dung câu lệnh. Ví dụ:\n`/ask Viết script python kiểm tra ip`",
            parse_mode="Markdown"
        )
        return

    prompt = " ".join(context.args).strip()
    await process_prompt(update, prompt)


@admin_only
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Xử lý tin nhắn văn bản tự do:
    - Nếu là bấm nút trên Reply Keyboard: Điều hướng tương ứng theo nút.
    - Tất cả các lệnh gõ tay bắt buộc phải có dấu / (ví dụ: /cd, /log, /status...).
    - Mọi văn bản thông thường khác: Tự động gửi làm câu lệnh prompt cho Antigravity.
    """
    text = update.message.text.strip() if update.message.text else ""
    if not text:
        return

    # Chỉ điều hướng khi người dùng nhấn đúng các phím bấm nhanh trên bàn phím (Reply Keyboard)
    if text == "📸 Chụp màn hình" or "Chụp màn hình" in text:
        from src.handlers.screen_handler import screen_handler
        return await screen_handler(update, context)
    elif text == "✨ Phiên mới" or "Phiên mới" in text:
        return await new_session_handler(update, context)
    elif "Đổi Model" in text:
        return await model_menu_handler(update, context)
    elif text == "📊 Trạng thái" or "Trạng thái" in text:
        from src.handlers.command_handler import status_handler
        return await status_handler(update, context)
    elif text == "📂 Thư mục" or "Thư mục" in text:
        context.args = []
        return await folder_command_handler(update, context)
    elif "Xem Log" in text:
        from src.handlers.command_handler import log_handler
        context.args = []
        return await log_handler(update, context)
    elif text == "🔒 Khóa máy" or "Khóa máy" in text:
        from src.handlers.power_handler import lock_handler
        return await lock_handler(update, context)
    elif text == "⛔ Tắt máy" or "Tắt máy" in text:
        from src.handlers.power_handler import shutdown_request_handler
        return await shutdown_request_handler(update, context)

    # Nếu không phải nút bấm Reply Keyboard, toàn bộ là prompt gửi sang Antigravity
    await process_prompt(update, text)


async def process_prompt(update: Update, prompt: str) -> None:
    """Gửi prompt cho Antigravity và phản hồi kết quả."""
    chat_id = update.effective_chat.id
    status_msg = await update.message.reply_text(
        f"🤖 **Antigravity đang xử lý...**\n"
        f"Model: `{agy_service.current_model}`\n"
        f"Chế độ: {'Tiếp tục phiên' if agy_service.continue_session else 'Phiên mới'}",
        parse_mode="Markdown"
    )

    await update.message.get_bot().send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    result = await agy_service.execute_prompt(prompt)

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_response_message(update, result)
