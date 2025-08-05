@echo off
echo Stopping Texas Hold'em GTO Trainer Docker container...

docker-compose down

if %errorlevel% equ 0 (
    echo Container stopped successfully!
) else (
    echo Error stopping container
)

pause