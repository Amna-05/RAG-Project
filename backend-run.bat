@echo off
REM Backend Development Server Launcher
REM Quick start command for FastAPI backend

echo ========================================
echo   RAG Backend - Development Server
echo ========================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Edit .env with your API keys before running!
    echo.
    pause
)

echo Setting Python path...
set PYTHONPATH=src

echo Activating virtual environment (if exists)...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Installing/updating dependencies...
call uv sync

echo.
echo Running database migrations...
call alembic upgrade head

echo.
echo Starting FastAPI development server...
echo Backend will be available at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

call uvicorn rag.main:app --reload --host 127.0.0.1 --port 8000

pause
