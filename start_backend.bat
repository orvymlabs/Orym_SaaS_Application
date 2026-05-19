@echo off
echo ========================================
echo Starting WhatsApp Bot Backend (Port 8001)
echo ========================================
echo.

cd backend

echo Checking Python installation...
python --version
echo.

echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8001
echo API Documentation: http://localhost:8001/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

pause
