@echo off
echo ========================================
echo Starting WhatsApp Bot Frontend (Port 3000)
echo ========================================
echo.

cd frontend

echo Checking Node.js installation...
node --version
echo.

echo Starting Next.js development server...
echo Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause
