@echo off
echo ========================================
echo    OVN STORE AI CHATBOT
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting chatbot server...
echo Open http://localhost:5000 in your browser
echo.
python server.py
