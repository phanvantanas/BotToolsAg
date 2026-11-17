# 🤖 ANTIGRAVITY TELEGRAM REMOTE BOT (AG-TELEBOT)

Hệ thống bot Telegram bảo mật cao giúp bạn giám sát và điều khiển **Antigravity CLI (agy)** cũng như máy tính Windows từ xa thông qua ứng dụng Telegram trên điện thoại (Android / iOS).

---

## 🚀 Tính năng chính

1. **Điều khiển Antigravity AI từ xa:**
   - Mặc định **giữ nguyên ngữ cảnh phiên hội thoại trước (`-c`)** để bot ghi nhớ mạch làm việc liên tục.
   - Nhắn tin văn bản tự nhiên bất kỳ để yêu cầu Antigravity xử lý tác vụ hoặc lập trình.
   - Lệnh `/new` hoặc nút **✨ Phiên mới**: Xóa sạch ngữ cảnh cũ để bắt đầu tác vụ mới.
   - Lệnh `/model` hoặc nút **⚙️ Đổi Model**: Chuyển đổi linh hoạt giữa các model AI (Gemini Flash, Claude Sonnet, Opus...), kèm kiểm tra hạn mức (*Quota*).
   - Tự động cắt tin nhắn thông minh hoặc đính kèm file `.txt` khi câu trả lời vượt quá giới hạn 4096 ký tự của Telegram.

2. **Chụp ảnh màn hình máy tính (Screenshot):**
   - Lệnh `/screen` hoặc nút **📸 Chụp màn hình**: Chụp tức thì màn hình máy tính và gửi ảnh chất lượng cao về Telegram.
   - Tự động xử lý tình huống màn hình bị khóa hoặc tắt hiển thị mà không làm gián đoạn bot.

3. **Quản lý nguồn máy tính từ xa:**
   - **Khóa máy (`/lock`):** Khóa màn hình máy tính ngay lập tức.
   - **Tắt máy (`/shutdown <PIN>`):** Yêu cầu nhập đúng mã PIN bảo mật cá nhân để kích hoạt đếm ngược tắt máy.
   - **Hủy lệnh (`/abort`):** Hủy lệnh tắt máy nếu đang trong thời gian đếm ngược.

4. **Bảo mật Zero-Trust:**
   - **Cơ chế Long Polling:** Hoạt động qua kênh bảo mật của Telegram, không cần mở cổng Router (NAT/Port Forwarding), tránh lộ IP gia đình.
   - **Whitelist User ID:** Chỉ những tài khoản có trong danh sách `ALLOWED_USER_IDS` mới có quyền tương tác. Tin nhắn từ người lạ sẽ bị **chặn và bỏ qua ngay lập tức (Drop silently)**, không phản hồi để tránh rò rỉ dữ liệu.
   - **Chống dò mã PIN (Anti Brute-Force):** Nhập sai mã PIN 3 lần liên tiếp sẽ tự động khóa lệnh nguy hiểm trong 5 phút.

---

## 📋 Yêu cầu hệ thống

- Hệ điều hành: **Windows 10 / 11**
- **Python 3.10+** (đã tích hợp vào PATH)
- Đã cài đặt **Antigravity CLI** (`agy`)
- Một tài khoản **Telegram** để tạo bot và nhận lệnh

---

## ⚙️ Hướng dẫn Cài đặt & Cấu hình

### Bước 1: Cài đặt các thư viện cần thiết
Mở terminal (PowerShell hoặc CMD) tại thư mục dự án và chạy:
```powershell
pip install -r requirements.txt
```

### Bước 2: Tạo file cấu hình `.env`
1. Tạo một bản sao từ file `.env.example` và đổi tên thành `.env`:
   ```powershell
   copy .env.example .env
   ```
2. Mở file `.env` bằng trình soạn thảo (Notepad, VS Code...) và điền các thông tin:

| Tên biến | Bắt buộc | Hướng dẫn lấy thông tin |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | **Có** | Mở Telegram, tìm bot **`@BotFather`**, gửi lệnh `/newbot` và làm theo hướng dẫn để nhận Token (dạng `123456789:AA...`). |
| `ALLOWED_USER_IDS` | **Có** | Mở Telegram, tìm bot **`@userinfobot`** và bấm Start. Bot sẽ gửi lại cho bạn `Id` của bạn (ví dụ: `123456789`). Điền ID này vào. Nếu có nhiều người dùng, ngăn cách bằng dấu phẩy `,`. |
| `SECURITY_PIN` | **Có** | Tự đặt 1 mã số bảo mật riêng (ví dụ: `2468`). Dùng để xác nhận khi gõ lệnh `/shutdown <PIN>`. |
| `DEFAULT_MODEL` | Không | Model AI mặc định (ví dụ: `gemini-3.8-flash-high`). |
| `AGY_PATH` | Không | Mặc định bot tự nhận diện theo thư mục: `C:\Users\<Tên_Bạn>\.gemini\bin\agy.exe`. Chỉ cần điền nếu bạn cài `agy.exe` ở vị trí khác. |

> [!WARNING]
> Tuyệt đối không xóa dòng `TELEGRAM_BOT_TOKEN` hoặc `ALLOWED_USER_IDS` trong `.env`. Bot sẽ từ chối khởi động nếu thiếu 2 thông số này để bảo vệ máy tính của bạn.

---

## 🚀 Hướng dẫn Khởi chạy & Quản lý Bot

### Cách 1: Tự động chạy ngầm cùng Windows (Khuyên dùng khi điều khiển từ xa)
Nhấp đúp chuột trực tiếp vào file:
👉 **[`cai_dat_tu_khoi_dong.bat`](file:///E:/tool/AG/cai_dat_tu_khoi_dong.bat)**

- Bot sẽ được đăng ký vào thư mục Windows Startup.
- Mỗi khi máy tính khởi động hoặc mở lại nguồn điện, bot sẽ **tự động chạy ngầm** (ẩn hoàn toàn cửa sổ đen terminal qua [`run_hidden.vbs`](file:///E:/tool/AG/run_hidden.vbs)) để sẵn sàng nhận lệnh.
- Khi muốn hủy tự khởi động: Chỉ cần nhấp đúp file **[`huy_tu_khoi_dong.bat`](file:///E:/tool/AG/huy_tu_khoi_dong.bat)**.

### Cách 2: Khởi chạy thủ công (Xem trực tiếp log trên màn hình)
Nhấp đúp chuột trực tiếp vào file:
👉 **[`start_bot.bat`](file:///E:/tool/AG/start_bot.bat)**

File `.bat` này đã tích hợp sẵn cơ chế kiểm tra môi trường `.env`, thiết lập font hiển thị tiếng Việt và theo dõi trạng thái bot.

### Cách 3: Khởi chạy bằng Terminal
```powershell
cd E:\tool\AG
python src\main.py
```

### 🛑 Cách dừng bot khi đang chạy ngầm
Nhấp đúp chuột trực tiếp vào file:
👉 **[`stop_bot.bat`](file:///E:/tool/AG/stop_bot.bat)**

Khi bot khởi động thành công, bạn chỉ cần mở Telegram trên điện thoại, tìm bot của mình và nhấn **Start** hoặc gõ `/menu`.

---

## 📱 Danh sách Lệnh & Phím tắt trên Telegram

### 💡 Gợi ý lệnh tự động khi gõ `/`
Bot đã tích hợp sẵn tính năng **Telegram Bot Commands**. Khi bạn gõ ký tự **`/`** vào khung chat hoặc bấm biểu tượng menu lệnh `[/]` trên Telegram, danh sách toàn bộ các lệnh kèm mô tả chi tiết sẽ **tự động hiện lên để bạn chọn nhanh** mà không cần nhớ cú pháp.

### ⌨️ Bàn phím tương tác nhanh (Reply Keyboard)
Hiển thị cố định ngay dưới khung chat gồm 8 phím tiện lợi:

| Phím tắt Menu | Lệnh tương ứng | Chức năng chi tiết |
|---|---|---|
| 📸 Chụp màn hình | `/screen` | Chụp ảnh màn hình máy tính gửi về điện thoại |
| ✨ Phiên mới | `/new` | Xóa ngữ cảnh cũ, bắt đầu phiên làm việc Antigravity mới |
| 📊 Trạng thái | `/status` | Xem % CPU, RAM, ổ đĩa C, thời gian uptime và model AI đang chọn |
| 📂 Thư mục | `/cd <path>` hoặc `/folder` | Xem hoặc chuyển thư mục làm việc hiện tại của Antigravity |
| ⚙️ Đổi Model (+ Quota) | `/model` | Bật menu chọn model AI kèm hiển thị 🟢/🔴 Quota và nút làm mới hạn mức |
| 📜 Xem Log | `/log` | Xem 25 dòng log mới nhất (hoặc `/log file` để tải toàn bộ file `bot.log`) |
| 🔒 Khóa máy | `/lock` | Khóa màn hình Windows ngay lập tức (`rundll32 user32.dll,LockWorkStation`) |
| ⛔ Tắt máy | `/shutdown <PIN>` | Bắt đầu đếm ngược 60 giây tắt máy tính (bắt buộc đúng mã PIN) |
| - | `/abort` | Hủy lệnh tắt máy tính đang đếm ngược |
| - | `/help` | Hiển thị bảng tóm tắt hướng dẫn sử dụng chi tiết |
| - | `/menu` | Mở lại bàn phím điều khiển nhanh nếu bị ẩn |

> [!TIP]
> **Quy tắc phân biệt lệnh và nội dung hỏi:**
> - Các lệnh điều khiển hệ thống **bắt buộc phải có dấu `/`** ở đầu (ví dụ: `/cd E:\tool\AG`, `/log`, `/status`...).
> - Mọi tin nhắn văn bản **không có dấu `/`** (ví dụ: *"viết script crawler python bằng selenium"*, *"cd vào thư mục test rồi build app"*...) đều được bot chuyển nguyên vẹn làm câu lệnh xử lý cho **Antigravity CLI**. Việc này giúp câu hỏi của bạn không bao giờ bị nhận nhầm thành lệnh điều khiển bot.

---

## 💡 Hướng dẫn Bật máy tính từ xa (Khi máy đã tắt)

Khi máy tính đã tắt nguồn hoàn toàn (Shutdown), phần mềm trên máy không thể tự chạy để nhận lệnh Telegram. Để có thể bật máy từ xa bằng điện thoại:

1. **Giải pháp tối ưu & ổn định nhất (Khuyên dùng):**
   - Trang bị 1 **ổ cắm thông minh** (Smart Plug Wi-Fi: Tuya, Sonoff, Tp-Link, Aqara... giá từ 80k - 150k).
   - Truy cập **BIOS/UEFI** của bo mạch chủ máy tính (nhấn `F2` hoặc `Del` khi vừa bật nguồn).
   - Tìm mục **AC Power Recovery** (hoặc *Restore on AC Power Loss* / *After Power Loss*) và đổi thành **Power On** (hoặc *Last State*).
   - Khi cần bật máy: Mở app trên điện thoại bật ổ cắm thông minh -> Máy tính sẽ tự động nhận diện có điện và khởi động vào Windows.
   - Kết hợp với việc chạy [`cai_dat_tu_khoi_dong.bat`](file:///E:/tool/AG/cai_dat_tu_khoi_dong.bat), bot sẽ tự động chạy ngầm cùng Windows ngay khi máy tính khởi động xong!
2. **Giải pháp Wake-on-LAN (WoL):**
   - Kích hoạt tính năng **Wake-on-LAN** trong BIOS và trong cấu hình Network Adapter của Windows.
   - Gửi gói tin Magic Packet từ Router hoặc một thiết bị luôn bật trong mạng nội bộ (như Raspberry Pi / TV Box) để đánh thức PC.

---

## 📄 Giấy phép & Đóng góp
Dự án được phát triển nhằm mục đích điều khiển cá nhân an toàn và tiện lợi. Mọi thắc mắc hoặc cải tiến vui lòng tạo Issue hoặc Pull Request.
