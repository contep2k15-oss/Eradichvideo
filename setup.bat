@echo off
REM ===========================================================
REM  Cai dat lan dau - chi can chay 1 lan duy nhat
REM  Bam dup vao file nay de tu dong tao venv + cai thu vien
REM ===========================================================

cd /d "%~dp0"

echo === Dang tao moi truong ao Python (venv)... ===
py -3.12 -m venv venv
if errorlevel 1 (
    echo.
    echo LOI: Khong tim thay Python 3.12. Hay chay lenh sau trong Git Bash truoc:
    echo     py install 3.12
    echo Sau do chay lai file setup.bat nay.
    pause
    exit /b 1
)

echo === Dang kich hoat venv va cai thu vien (co the mat vai phut)... ===
call venv\Scripts\activate.bat
pip install -r requirements.txt

if not exist ".env" (
    echo === Chua co file .env, dang tao tu .env.example... ===
    copy .env.example .env
    echo.
    echo QUAN TRONG: Mo file .env vua tao va dien API key that vao truoc khi dung.
)

echo.
echo ===========================================================
echo  Cai dat xong! Tu gio chi can bam dup vao "start.bat" de chay app.
echo ===========================================================
pause
