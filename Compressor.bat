@echo off
cd /d %~dp0
start "" cmd /c "python ./main.py %* & timeout /t 10 & exit"
exit