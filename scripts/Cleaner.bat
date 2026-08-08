@echo off

Title Deep Cleaner

del /f /s /q %temp%\*
del /f /s /q C:\Windows\Temp\*
del /f /s /q C:\Windows\Prefetch\*

echo Cleanup Complete.
pause
