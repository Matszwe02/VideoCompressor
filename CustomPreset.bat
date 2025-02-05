@echo off
cd /d %~dp0
start "" cmd /c "python ./main.py -40HEfanh %* & timeout /t 10 & exit"
exit