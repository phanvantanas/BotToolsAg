# TÀI LIỆU ĐẶC TẢ KỸ THUẬT (SPECIFICATION)
## DỰ ÁN: ANTIGRAVITY TELEGRAM REMOTE BOT (AG-TELEBOT)

---

## 1. Mục tiêu Dự án (Objective)

Hệ thống **AG-Telebot** là một ứng dụng chạy ngầm trên máy tính Windows cá nhân, kết nối với Telegram Bot API nhằm cho phép người dùng điều khiển **Antigravity CLI** và máy tính từ xa thông qua ứng dụng Telegram trên điện thoại (Android / iOS) với tiêu chuẩn bảo mật tối đa.

### Yêu cầu cốt lõi từ người dùng:
1. **Điều khiển Antigravity**: Gửi câu lệnh / prompt cho Antigravity CLI (`agy.exe`), nhận tiến trình và kết quả trả về ngay trong khung chat Telegram.
2. **Chụp ảnh màn hình (Screenshot)**: Chụp toàn bộ màn hình desktop hoặc chụp riêng cửa sổ Antigravity/trình duyệt đang mở, gửi ảnh nét cao qua Telegram để giám sát từ xa.
3. **Quản lý nguồn máy tính (Power Management)**:
   - *Tắt máy / Khóa máy*: Thực thi an toàn với xác thực mã PIN và cơ chế hủy lệnh kịp thời.
   - *Mở máy*: Cung cấp giải pháp Wake-on-LAN (WoL) và cấu hình AC Recovery qua Smart Plug.
4. **Bảo mật tối đa (High Security Priority)**:
   - Chống tuyệt đối truy cập trái phép từ người lạ trên Telegram.
   - Whitelist duy nhất theo Telegram User ID (chat_id).
   - Mã PIN xác thực cho các lệnh quan trọng (Tắt máy, chạy lệnh OS nhạy cảm).
   - Bảo mật tệp cấu hình `.env`, không lộ token hay thông tin định danh.

---

## 2. Các giả định ban đầu (Assumptions)

1. Máy tính chạy hệ điều hành **Windows 10/11**, đã cài sẵn **Python 3.11+** và **Antigravity CLI** tại `C:\Users\Bao\.gemini\bin\agy.exe`.
2. Người dùng đã có tài khoản Telegram và có thể tạo Bot Token thông qua `@BotFather`.
3. Người dùng biết Telegram User ID của chính mình (có thể lấy qua bot `@userinfobot`).
4. **Về việc Bật máy từ xa khi máy đã tắt hoàn toàn**:
   - Khi máy tính tắt hẳn (Power Off), phần mềm trên máy không thể hoạt động. Để bật máy từ xa, giải pháp thực tế khả thi là:
     - **Cách 1 (Khuyên dùng)**: Kết hợp Smart Plug (Ổ cắm thông minh Tuya/Sonoff) + Bật tính năng *AC Power Recovery / Restore on AC Power Loss* trong BIOS của bo mạch chủ.
     - **Cách 2**: Wake-on-LAN (WoL) gửi gói Magic Packet từ một thiết bị nội mạng (như Router OpenWrt, Raspberry Pi, hoặc điện thoại kết nối VPN vào mạng nhà).
   - Bot trên máy chủ này sẽ chịu trách nhiệm chính về: Tắt máy (kèm mã PIN), Khóa màn hình và kiểm tra trạng thái hoạt động.

---

## 3. Kiến trúc Hệ thống & Mô hình Bảo mật (Security & Architecture)

### 3.1. Sơ đồ Kiến trúc Tổng thể

```
[ Điện thoại Android (Telegram App) ]
                 │
                 │ (HTTPS / TLS qua Telegram Bot API)
                 ▼
     [ Telegram Cloud Servers ]
                 │
                 │ (Long Polling an toàn - Không cần mở port / NAT router)
                 ▼
  [ Windows Host: AG-Telebot Daemon ]
    ├── (1) Security Guard (Whitelist User ID + Rate Limiter + OTP/PIN)
    ├── (2) Command Router & UI Keyboard
    ├── (3) Antigravity Bridge (Gọi agy.exe CLI / Stream output / Quản lý session)
    ├── (4) Screen Capture Module (Chụp màn hình đa màn hình bằng mss/Pillow)
    └── (5) System Control Module (Shutdown / Lock / Status)
```

### 3.2. Mô hình Bảo mật Chuyên sâu (Security Architecture)

1. **Cơ chế Long Polling**:
   - Bot hoạt động theo mô hình *Long Polling* kéo dữ liệu từ máy chủ Telegram về máy tính. **Không cần mở port router, không cần dùng ngrok, không cần IP tĩnh**, do đó triệt tiêu hoàn toàn nguy cơ bị quét port (port scan) hay tấn công DDoS vào mạng gia đình.
2. **Whitelist Telegram User ID (Bắt buộc)**:
   - File cấu hình chỉ chấp nhận danh sách ID cụ thể (ví dụ: `ALLOWED_USER_IDS=[123456789]`).
   - Mọi tin nhắn hoặc lệnh từ bất kỳ ID nào không nằm trong danh sách sẽ bị **bỏ qua ngay lập tức ở tầng filter**, không phản hồi (Drop silently) để tránh kẻ tấn công biết bot đang hoạt động, đồng thời ghi log cảnh báo về máy tính.
3. **Xác thực 2 bước (PIN Code Confirmation)**:
   - Các lệnh nhạy cảm như `/shutdown` yêu cầu nhập mã PIN bảo mật.
4. **Giới hạn tốc độ lệnh (Rate Limiting) & Chống Brute Force**:
   - Giới hạn tối đa 5 yêu cầu/phút đối với các tác vụ nặng (chụp ảnh, gọi AI).
   - Nếu nhập sai PIN 3 lần, tự động khóa tương tác trong 15 phút và gửi cảnh báo về console.
5. **Cách ly biến môi trường & Quản lý Log**:
   - File `.env` chứa `BOT_TOKEN`, `ALLOWED_USER_IDS`, `SECURITY_PIN`. File này nằm trong danh sách `.gitignore`.
   - Log ghi nhận chi tiết thời gian, lệnh thực thi, nhưng làm mờ (mask) nội dung token và mật khẩu.

---

## 4. Công nghệ & Thư viện sử dụng (Tech Stack)

| Thành phần | Công nghệ / Thư viện | Lý do lựa chọn |
|---|---|---|
| **Ngôn ngữ** | Python 3.11+ | Hiệu năng ổn định trên Windows, tích hợp tốt với Antigravity. |
| **Telegram Framework** | `python-telegram-bot` (v21+ async) | Hỗ trợ bất đồng bộ (asyncio), xử lý mượt mà tác vụ dài mà không nghẽn bot. |
| **Chụp ảnh màn hình** | `mss` & `Pillow` | Tốc độ chụp siêu nhanh (< 50ms), hỗ trợ đa màn hình, nén ảnh JPEG tối ưu dung lượng gửi qua Telegram. |
| **Giao tiếp Antigravity** | `subprocess` (asyncio) / CLI Wrapper | Tương thích trực tiếp với `C:\Users\Bao\.gemini\bin\agy.exe`. |
| **Quản lý cấu hình** | `pydantic-settings` / `python-dotenv` | Xác thực kiểu dữ liệu nghiêm ngặt, tự động kiểm tra token và user ID khi khởi động. |
| **Kiểm thử tự động** | `pytest`, `pytest-asyncio`, `pytest-mock` | Phục vụ quy trình TDD (Test-Driven Development). |

---

## 5. Cấu trúc Dự án (Project Structure)

```
e:\tool\AG\
│
├── .env.example               # Mẫu cấu hình môi trường
├── .env                       # Cấu hình thực tế (chứa Token, ID - cấm commit)
├── .gitignore                 # Bỏ qua venv, .env, __pycache__, temp/
├── README.md                  # Hướng dẫn cài đặt và sử dụng (Tiếng Việt)
├── SPEC.md                    # Tài liệu đặc tả kỹ thuật này
├── requirements.txt           # Danh sách thư viện Python
├── start_bot.bat              # Script khởi chạy bot có kiểm tra môi trường
├── stop_bot.bat               # Script dừng bot an toàn
├── run_hidden.vbs             # Khởi chạy bot ẩn cửa sổ console
├── cai_dat_tu_khoi_dong.bat   # Đăng ký bot tự động chạy ngầm cùng Windows (Startup)
├── huy_tu_khoi_dong.bat       # Hủy tự khởi động cùng Windows
│
├── temp/                      # Thư mục chứa log (bot.log) và ảnh chụp màn hình tạm
│
├── src/                       # Mã nguồn chính
│   ├── __init__.py
│   ├── main.py                # Điểm khởi chạy Bot & cơ chế Single Instance Mutex
│   ├── config.py              # Xử lý cấu hình và kiểm tra biến môi trường
│   │
│   ├── core/                  # Tầng bảo mật và lõi xử lý
│   │   ├── __init__.py
│   │   ├── security.py        # Middleware kiểm tra Whitelist ID, Rate limit, PIN
│   │   └── logger.py          # Hệ thống ghi log an toàn (Rolling File Handler)
│   │
│   ├── handlers/              # Điều hướng các lệnh Telegram
│   │   ├── __init__.py
│   │   ├── command_handler.py # Xử lý /start, /menu, /help, /status, /log và Reply Keyboard
│   │   ├── agy_handler.py     # Nhận prompt, /ask, /new, /model (quota), /cd và tin nhắn tự do
│   │   ├── screen_handler.py  # Xử lý chụp và gửi ảnh màn hình
│   │   └── power_handler.py   # Xử lý tắt máy (kèm mã PIN), khóa màn hình và nút hủy /abort
│   │
│   └── services/              # Dịch vụ hệ thống nền tảng
│       ├── __init__.py
│       ├── agy_service.py     # Wrapper tương tác với agy.exe CLI, quản lý session & quota cache
│       ├── screen_service.py  # Chụp ảnh màn hình bằng mss/ImageGrab/Task Scheduler ẩn
│       └── power_service.py   # Lệnh hệ điều hành Windows (shutdown, rundll32, lock, uptime)
│
└── tests/                     # Kiểm thử tự động (Pytest)
    ├── __init__.py
    ├── conftest.py            # Fixtures dùng chung cho tests
    ├── test_security.py       # Kiểm thử xác thực Whitelist và chặn người lạ
    ├── test_agy_service.py    # Kiểm thử giao tiếp Antigravity CLI & quota
    ├── test_screen_service.py # Kiểm thử chụp ảnh màn hình
    ├── test_power_service.py  # Kiểm thử lệnh nguồn hệ thống an toàn
    └── test_interactive_handlers.py # Kiểm thử menu tương tác, phiên mới, quota, log, thư mục
```

---

## 6. Giao diện & Danh sách Lệnh trên Telegram (Bot UX & Commands)

Hệ thống hỗ trợ cả **giao diện phím bấm nhanh (Reply Keyboard)** tiện lợi lẫn **gợi ý lệnh tự động khi gõ `/`**:
- **Gợi ý tự động (Bot Commands Suggestion)**: Đăng ký danh sách `BotCommand` qua cơ chế `post_init` (`set_my_commands`). Khi người dùng gõ ký tự `/` hoặc bấm nút `[/]` trên Telegram, toàn bộ danh sách lệnh kèm mô tả sẽ tự động hiện lên để người dùng chọn nhanh.
- **Phân định rõ ràng**: Mọi lệnh điều khiển gõ tay bắt buộc phải có dấu `/` ở đầu (ví dụ: `/cd <path>`, `/log`, `/status`...). Mọi tin nhắn không bắt đầu bằng `/` sẽ được chuyển trực tiếp cho Antigravity CLI làm prompt xử lý.

| Lệnh | Phím bấm Menu | Chức năng chi tiết | Cơ chế bảo mật |
|---|---|---|---|
| `/start` | - | Khởi động bot, gửi lời chào và bật bàn phím điều khiển | Kiểm tra Whitelist |
| `/menu` | - | Mở lại bàn phím điều khiển nhanh | Kiểm tra Whitelist |
| `/ask <prompt>` (hoặc nhắn trực tiếp) | - | Ra lệnh cho Antigravity AI (mặc định giữ ngữ cảnh `-c`) | Giới hạn ký tự + Whitelist |
| `/screen` | 📸 Chụp màn hình | Chụp tức thì màn hình máy tính gửi về điện thoại | Whitelist + Rate limit |
| `/new` | ✨ Phiên mới | Bắt đầu phiên làm việc mới (xóa sạch ngữ cảnh cũ) | Whitelist |
| `/status` | 📊 Trạng thái | Báo cáo % CPU, RAM, ổ đĩa C, uptime, model và tiến trình | Whitelist |
| `/cd <path>` hoặc `/folder` / `/pwd` | 📂 Thư mục | Xem hoặc chuyển thư mục làm việc hiện tại của bot | Whitelist |
| `/model` | ⚙️ Đổi Model (+ Quota) | Mở menu chọn model AI tích hợp đo hạn mức (🟢/🔴 Quota) | Whitelist |
| `/log` hoặc `/logs` | 📜 Xem Log | Xem 25 dòng log mới nhất hoặc tải toàn bộ file (`/log file`) | Whitelist |
| `/lock` | 🔒 Khóa máy | Khóa màn hình Windows ngay lập tức (`LockWorkStation`) | Whitelist |
| `/shutdown [PIN]` | ⛔ Tắt máy | Đếm ngược tắt máy (yêu cầu đúng mã PIN bảo mật) | **Bắt buộc mã PIN** |
| `/abort` | - | Hủy ngay lệnh tắt máy đang đếm ngược | Whitelist |
| `/help` | - | Hiển thị hướng dẫn chi tiết các lệnh | Whitelist |

---

## 7. Quy ước Mã nguồn & Code Style (Code Style Guidelines)

- **Ngôn ngữ lập trình**: Python 3.11+ có Type Hinting đầy đủ (`typing`).
- **Async/Await**: Toàn bộ luồng Telegram và Subprocess đều dùng `asyncio` để không bao giờ block tiến trình chính.
- **Xử lý ngoại lệ**: Bắt buộc `try...except` ở mọi handler và gửi thông báo lỗi thân thiện về Telegram thay vì để bot crash.
- **Cơ chế Single Instance**: Dùng socket mutex nội bộ port 49281 để ngăn chặn lỗi chạy nhiều bot gây Telegram Conflict.
- **Ví dụ phong cách code**:
```python
# src/core/security.py
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.config import settings

logger = logging.getLogger(__name__)

def admin_only(func):
    """Decorator đảm bảo chỉ Telegram User ID được cấp phép mới thực thi được lệnh."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if user_id not in settings.ALLOWED_USER_IDS:
            logger.warning(f"Cảnh báo bảo mật: Phát hiện User ID không hợp lệ cố truy cập: {user_id}")
            # Drop silently: Không trả lời người lạ để tránh lộ sự tồn tại của bot
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
```

---

## 8. Chiến lược Kiểm thử (Testing Strategy - TDD)

Áp dụng quy trình kiểm thử trước (Test-Driven Development) với 100% test case xanh (21/21 passed):
1. **Kiểm thử Bảo mật (`test_security.py`)**:
   - Test user trong Whitelist -> Cho phép truy cập.
   - Test user lạ -> Chặn 100%, không phản hồi tin nhắn.
   - Test nhập sai PIN quá 3 lần -> Tự động khóa chống Brute-Force.
2. **Kiểm thử Antigravity Wrapper (`test_agy_service.py`)**:
   - Mock lệnh `agy.exe --print "test prompt"`, kiểm tra bắt output stdout/stderr và timeout.
   - Kiểm tra cơ chế giữ/reset ngữ cảnh phiên (`continue_session`).
   - Kiểm tra bộ đệm Quota Cache và phát hiện trạng thái model hết hạn mức.
3. **Kiểm thử Chụp màn hình (`test_screen_service.py`)**:
   - Kiểm tra pipeline 3 tầng (mss -> ImageGrab -> VBScript/Task Scheduler).
   - Kiểm tra định dạng byte buffer JPEG hợp lệ trước khi gửi qua Telegram.
4. **Kiểm thử Quản lý nguồn (`test_power_service.py`)**:
   - Mock các hàm gọi OS (`subprocess.run`), đảm bảo chỉ sinh đúng tham số tắt máy an toàn khi đã qua xác thực PIN.
   - Kiểm tra hủy lệnh tắt máy `/abort`.
5. **Kiểm thử Tương tác người dùng (`test_interactive_handlers.py`)**:
   - Kiểm tra toàn bộ luồng tương tác thực tế: Tạo phiên mới (`/new`), Báo cáo phần cứng (`/status`), Menu chọn model & kiểm tra quota (`/model`), Quản lý thư mục (`/cd`), Xem log (`/log`, `/log file`), Bàn phím điều khiển Reply Keyboard, phím tắt `📜 Xem Log` và danh sách gợi ý tự động `BOT_COMMANDS`.

---

## 9. Ranh giới Hành động (Boundaries)

- **Luôn luôn làm**:
  - Kiểm tra User ID ở tầng đầu tiên của mọi request.
  - Sử dụng phím bấm xác nhận 2 bước cho các thao tác tắt/khởi động lại máy.
  - Sử dụng buffer bộ nhớ tạm khi chụp ảnh màn hình, tự giải phóng RAM sau khi gửi.
  - Viết code có chú thích rõ ràng bằng Tiếng Việt.
- **Cần hỏi ý kiến người dùng trước**:
  - Khi cần cài thêm package hệ thống đặc thù ngoài danh sách thiết kế.
  - Thay đổi cổng hoặc cơ chế kết nối.
- **Tuyệt đối không làm**:
  - Không bao giờ lưu cứng Token hoặc User ID trực tiếp vào mã nguồn.
  - Không bao giờ cho phép người lạ kích hoạt lệnh dù dưới bất kỳ hình thức nào.
  - Không xóa bất kỳ dữ liệu hay cơ sở dữ liệu nào của hệ thống.
