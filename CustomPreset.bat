@echo off
cd /d %~dp0
start "" cmd /c "python ./main.py -40HEfan %* & timeout /t 10 & exit"
exit