@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title AG-Telebot - Điều khiển Antigravity từ xa
echo ========================================================
echo    ĐANG KHỞI CHẠY ANTIGRAVITY TELEGRAM REMOTE BOT
echo ========================================================
cd /d "%~dp0"

:: Kiểm tra file .env
if not exist ".env" (
    echo [LỖI] Không tìm thấy file .env!
    echo Vui lòng copy từ .env.example và điền Bot Token của bạn vào .env.
    pause
    exit /b 1
)

python src\main.py
if errorlevel 1 (
    echo.
    echo [CẢNH BÁO] Bot bị dừng do lỗi! Vui lòng kiểm tra file log tại temp\bot.log
    pause
)
