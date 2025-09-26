@echo off
REM --- This script removes the scheduled task that auto-restarts TWS ---

schtasks /Delete /TN "Restart TWS" /F
echo Scheduled task 'Restart TWS' has been removed.
pause
