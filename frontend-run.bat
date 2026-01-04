@echo off
REM Frontend Development Server Launcher
REM Quick start command for Next.js frontend

echo ========================================
echo   RAG Frontend - Development Server
echo ========================================
echo.

cd frontend\rag-frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    echo.
)

REM Check for .env.local
if not exist ".env.local" (
    echo Creating .env.local with default settings...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 > .env.local
    echo.
)

echo Starting development server...
echo Frontend will be available at: http://localhost:3000
echo API Backend at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev

pause
