@echo off

echo ==========================================
echo        PocketSmart AI
echo ==========================================

if not exist ".venv" (
    echo Virtual environment not found.
    echo Create it using:
    echo python -m venv .venv
    pause
    exit /b
)

call .venv\Scripts\activate

echo Starting PocketSmart AI...

uvicorn app.main:app --reload

pause