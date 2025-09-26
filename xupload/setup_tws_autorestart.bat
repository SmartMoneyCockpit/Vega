@echo off
REM --- This script creates a scheduled task to restart TWS daily ---

REM Kill any running TWS/javaw processes and restart using your starter.bat
schtasks /Create /SC DAILY /TN "Restart TWS" /TR "cmd /c taskkill /IM javaw.exe /F & C:\Jts\starter.bat" /ST 03:30 /F
