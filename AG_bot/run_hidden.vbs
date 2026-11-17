Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\tool\AG"
WshShell.Run "cmd.exe /c start_bot.bat", 0, False
