@echo off
echo Preparing Texas Hold'em GTO Trainer for Zeabur deployment...
echo.

REM 檢查是否已經初始化 Git 倉庫
if not exist ".git" (
    echo Initializing Git repository...
    git init
    if %errorlevel% neq 0 (
        echo Error: Git is not installed or not in PATH
        echo Please install Git from https://git-scm.com/
        pause
        exit /b 1
    )
) else (
    echo Git repository already initialized.
)

REM 添加所有檔案到 Git
echo Adding files to Git...
git add .

REM 檢查是否有變更需要提交
git diff --cached --quiet
if %errorlevel% neq 0 (
    echo Committing changes...
    git status
    echo.
    set /p commit_message="Enter commit message (or press Enter for default): "
    if "%commit_message%"=="" set commit_message=Prepare Texas Hold'em GTO Trainer for Zeabur deployment
    git commit -m "%commit_message%"
) else (
    echo No changes to commit.
)

echo.
echo ================================
echo Git repository is ready!
echo.
echo Next steps for Zeabur deployment:
echo.
echo 1. Push to GitHub/GitLab:
echo    git remote add origin [YOUR_REPO_URL]
echo    git push -u origin main
echo.
echo 2. Visit https://dash.zeabur.com
echo 3. Click "New Project" and select "Deploy from Git"
echo 4. Choose your repository
echo 5. Zeabur will automatically detect and deploy your app!
echo.
echo For detailed instructions, see ZEABUR_README.md
echo ================================
echo.

pause