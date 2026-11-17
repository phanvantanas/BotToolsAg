@echo off
chcp 65001 >nul
echo ========================================================
echo    HỦY TỰ ĐỘNG CHẠY CÙNG WINDOWS CHO AG-TELEBOT
echo ========================================================

set LINK_PATH="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AG-Telebot.lnk"

if exist %LINK_PATH% (
    del %LINK_PATH%
    echo [THÀNH CÔNG] Đã xóa bot khỏi danh sách tự khởi động cùng Windows.
) else (
    echo [THÔNG BÁO] Bot chưa được cài tự khởi động trước đó.
)

echo.
pause
