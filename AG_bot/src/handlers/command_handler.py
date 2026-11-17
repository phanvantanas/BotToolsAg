from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from src.core.security import admin_only
from src.services.power_service import power_service
from src.services.agy_service import agy_service


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Tạo bàn phím điều khiển nhanh (Reply Keyboard) cho điện thoại Android."""
    keyboard = [
        [KeyboardButton("📸 Chụp màn hình"), KeyboardButton("✨ Phiên mới")],
        [KeyboardButton("📊 Trạng thái"), KeyboardButton("📂 Thư mục")],
        [KeyboardButton("⚙️ Đổi Model (+ Quota)"), KeyboardButton("📜 Xem Log")],
        [KeyboardButton("🔒 Khóa máy"), KeyboardButton("⛔ Tắt máy")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


@admin_only
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /start."""
    user = update.effective_user
    name = user.first_name if user else "Bạn"

    welcome_text = (
        f"👋 **Xin chào {name}!**\n\n"
        f"🤖 **Antigravity Remote Bot** đã sẵn sàng điều khiển máy tính của bạn an toàn từ xa.\n\n"
        f"💡 **Cách sử dụng:**\n"
        f"• Nhắn trực tiếp nội dung hoặc dùng `/ask <câu lệnh>` để ra lệnh cho Antigravity.\n"
        f"• Mặc định bot sẽ **giữ ngữ cảnh phiên trước**.\n"
        f"• Bấm **✨ Phiên mới** khi bạn muốn bắt đầu một câu chuyện/nhiệm vụ mới.\n"
        f"• Bấm **📸 Chụp màn hình** để xem trực tiếp desktop.\n"
        f"• Bấm **⚙️ Đổi Model (+ Quota)** để xem quota từng model và chuyển đổi.\n"
        f"• Bấm **📜 Xem Log** để theo dõi nhật ký hoạt động.\n"
        f"• Các nút điều khiển máy tính nằm ngay trên bàn phím bên dưới."
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@admin_only
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mở lại bảng điều khiển nhanh."""
    await update.message.reply_text(
        "📋 **Bảng điều khiển nhanh:**",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@admin_only
async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xem trạng thái hệ thống và Antigravity."""
    stats = power_service.get_system_stats()
    agy_info = agy_service.get_status_info()

    status_text = (
        f"📊 **BÁO CÁO TRẠNG THÁI HỆ THỐNG**\n"
        f"─────────────────────\n"
        f"💻 **Phần cứng máy tính:**\n"
        f"• **CPU:** {stats.get('cpu_percent', 'N/A')}%\n"
        f"• **RAM:** {stats.get('ram_used_gb', 'N/A')}/{stats.get('ram_total_gb', 'N/A')} GB"
        f" ({stats.get('ram_percent', 'N/A')}%)\n"
        f"• **Ổ đĩa C:** Trống {stats.get('disk_free_gb', 'N/A')} GB"
        f" ({100 - stats.get('disk_percent', 0):.1f}% còn trống)\n"
        f"• **Uptime:** {stats.get('uptime', 'N/A')}\n\n"
        f"🤖 **Antigravity AI Engine:**\n"
        f"• **Model đang dùng:** `{agy_info['model_name']}`\n"
        f"• **Ngữ cảnh:** {agy_info['session_mode']}\n"
        f"• **Thư mục:** `{agy_info['working_dir']}`\n"
        f"• **Tiến trình:** {'⏳ Đang bận' if agy_info['is_busy'] else '✅ Sẵn sàng'}\n"
        f"─────────────────────\n"
        f"👉 `/model` — đổi model & kiểm tra quota từng model."
    )

    await update.message.reply_text(status_text, parse_mode="Markdown")


@admin_only
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hướng dẫn chi tiết các lệnh."""
    help_text = (
        f"📖 **HƯỚNG DẪN CÁC LỆNH ĐIỀU KHIỂN:**\n\n"
        f"🤖 **Tương tác với Antigravity:**\n"
        f"• Nhắn trực tiếp hoặc `/ask <nội dung>` để gửi lệnh cho Antigravity.\n"
        f"• `/new` — Bắt đầu phiên mới (xóa ngữ cảnh cũ).\n"
        f"• `/cd <đường_dẫn>` hoặc `/folder` — Xem/đổi thư mục làm việc.\n"
        f"• `/model` — Chọn model AI, xem 🟢/🔴 quota từng model ngay trên menu.\n\n"
        f"🖥️ **Giám sát & Nguồn máy tính:**\n"
        f"• `/screen` — Chụp ảnh màn hình gửi về điện thoại.\n"
        f"• `/status` — Xem CPU, RAM, ổ cứng, model đang dùng.\n"
        f"• `/log` — Xem nhật ký hoạt động gần nhất (hoặc `/log file` để tải về).\n"
        f"• `/lock` — Khóa màn hình ngay lập tức.\n"
        f"• `/shutdown` — Tắt máy (yêu cầu xác thực mã PIN).\n"
        f"• `/abort` — Hủy lệnh tắt máy đang đếm ngược."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


@admin_only
async def log_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Xem log hệ thống trực tiếp từ Telegram:
    - /log: Xem 25 dòng log mới nhất.
    - /log <số_dòng>: Xem N dòng log (5 - 100 dòng).
    - /log file: Gửi toàn bộ file bot.log đính kèm.
    """
    from pathlib import Path

    log_file = Path(__file__).resolve().parent.parent.parent / "temp" / "bot.log"
    if not log_file.exists():
        await update.message.reply_text("ℹ️ Chưa có file log nào được tạo.")
        return

    arg = context.args[0].lower() if context.args else ""

    # Gửi file log đính kèm nếu yêu cầu
    if arg in ("file", "all", "full"):
        try:
            with open(log_file, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename="bot.log",
                    caption="📄 Toàn bộ file nhật ký hoạt động (bot.log)."
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Không thể đọc file log: {e}")
        return

    # Đọc N dòng cuối
    num_lines = 25
    if arg.isdigit():
        num_lines = max(5, min(int(arg), 100))

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if not lines:
            await update.message.reply_text("ℹ️ File log hiện đang trống.")
            return

        last_lines = lines[-num_lines:]
        content = "".join(last_lines).strip()

        # Cắt ngắn nếu vượt ngưỡng an toàn tin nhắn Telegram
        if len(content) > 3800:
            content = content[-3800:]

        header = f"📜 **{len(last_lines)} DÒNG LOG MỚI NHẤT:**\n"
        await update.message.reply_text(
            f"{header}```text\n{content}\n```\n💡 _Dùng `/log file` để tải toàn bộ file log_",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi đọc log: {e}")
