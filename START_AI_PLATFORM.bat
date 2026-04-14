@echo off
echo ========================================================
echo AJEL CAPITAL NEURAL PLATFORM BOOT SEQUENCE
echo ========================================================
echo Checking Docker Desktop status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop first!
    pause
    exit /b
)

echo Starting PostgreSQL, Redis, FastAPI Brain, and NextJS UI...
docker-compose up -d --build

echo ========================================================
echo BOOT SUCCESSFUL!
echo ========================================================
echo Frontend UI running at: http://localhost:3000
echo API Brain running at:   http://localhost:8000/docs
echo Database running at:    localhost:5432
echo.
pause
