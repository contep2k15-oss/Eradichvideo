@echo off
REM ===========================================================
REM  Khoi dong app - bam dup vao file nay moi lan muon dung tool
REM  (chay setup.bat truoc neu day la lan dau tien)
REM ===========================================================

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo LOI: Chua cai dat. Hay bam dup vao "setup.bat" truoc, chi can lam 1 lan.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo === Dang khoi dong server... ===
echo (Cua so nay phai giu nguyen mo trong luc dung app. Dong cua so = tat app.)
echo.

REM Mo trinh duyet sau 3 giay (du thoi gian server khoi dong xong)
start "" cmd /c "timeout /t 3 >nul && start http://localhost:8000"

uvicorn backend.main:app --port 8000

pause
