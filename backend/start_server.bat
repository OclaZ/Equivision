@echo off
cd /d "%~dp0"
echo ==========================================
echo   EquiVision Server Loader
echo ==========================================

echo [1/4] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is NOT running! Please start Docker Desktop and try again.
    pause
    exit /b
)
echo Docker is running.

echo [2/4] Starting Database Container...
docker  start equivision-db >nul 2>&1
if %errorlevel% neq 0 (
    echo Container equivision-db not found. Creating it...
    docker run -d --name equivision-db -e POSTGRES_PASSWORD=equivision123 -e POSTGRES_DB=equivision_db -p 5433:5432 postgres:15
) else (
    echo Database started.
)

echo [3/4] Starting ML Backend Container...
docker start equivision-ml-backend >nul 2>&1
if %errorlevel% neq 0 (
     echo Container equivision-ml-backend not found. Creating it...
     echo NOTE: Ensure you have built 'equivision-backend-serve' image. 
     docker run -d -p 8001:8000 --name equivision-ml-backend -e ML_MODE=VISION_ONLY -v "%cd%":/app equivision-backend-serve
) else (
     echo ML Backend started.
)

echo [4/4] Starting Local API Server...
echo The server will run on http://localhost:8000
echo.
venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
