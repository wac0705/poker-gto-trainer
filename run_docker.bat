@echo off
echo Building and starting Texas Hold'em GTO Trainer (Enhanced UI) in Docker...
echo.

REM 檢查 Docker 是否安裝
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM 檢查 Docker 是否運行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop
    pause
    exit /b 1
)

echo Building Docker image...
docker-compose build

if %errorlevel% neq 0 (
    echo Error: Failed to build Docker image
    pause
    exit /b 1
)

echo Starting container...
docker-compose up -d

if %errorlevel% neq 0 (
    echo Error: Failed to start container
    pause
    exit /b 1
)

echo.
echo ================================
echo Texas Hold'em GTO Trainer is now running in Docker!
echo.
echo Access the application at: http://localhost:8501
echo.
echo To stop the application, run: docker-compose down
echo To view logs, run: docker-compose logs -f
echo ================================
echo.

REM 等待服務啟動
echo Waiting for service to start...
timeout /t 5 /nobreak >nul

REM 嘗試打開瀏覽器
start http://localhost:8501

pause