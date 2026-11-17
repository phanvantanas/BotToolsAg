@echo off
chcp 65001 >nul
echo ========================================================
echo    CÀI ĐẶT AG-TELEBOT TỰ ĐỘNG CHẠY CÙNG WINDOWS
echo ========================================================

set SCRIPT="%TEMP%\create_ag_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AG-Telebot.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "wscript.exe" >> %SCRIPT%
echo oLink.Arguments = """E:\tool\AG\run_hidden.vbs""" >> %SCRIPT%
echo oLink.WorkingDirectory = "E:\tool\AG" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo [THÀNH CÔNG] Đã bật tự khởi động cùng máy tính!
echo Mỗi khi bạn bật PC lên, bot sẽ tự động chạy ngầm mà không cần bạn phải bấm gì cả.
echo.
pause
