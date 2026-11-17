@echo off
chcp 65001 >nul
echo ========================================
echo       ĐANG DỪNG AG-TELEBOT
echo ========================================
wmic process where "commandline like '%%src\\main.py%%'" call terminate >nul 2>&1
echo [OK] Đã dừng bot thành công!
timeout /t 3 >nul
