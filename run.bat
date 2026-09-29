@echo off
setlocal
call "%ProgramData%\anaconda3\Scripts\activate.bat" fdd_eval
cd /d "%~dp0"
python -m fdd_eval
endlocal
