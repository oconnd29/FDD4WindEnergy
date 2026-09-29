@echo off
setlocal
call "%ProgramData%\anaconda3\Scripts\activate.bat" fdd_eval
cd /d "%~dp0"
python scripts\make_icon.py
python -m pip install --quiet pyinstaller
python -m PyInstaller --noconfirm FDD_Evaluation.spec
echo Built dist\FDD_Evaluation.exe
endlocal
