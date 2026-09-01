@echo off
echo ========================================
echo Cell Site Mapping - Quick GitHub Deploy
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Initializing Git repository...
git init
if errorlevel 1 (
    echo Git initialization failed. Is Git installed?
    pause
    exit /b 1
)

echo [2/3] Adding all files...
git add .
git commit -m "Initial commit: Cell Site Mapping & Analytics System"

echo.
echo [3/3] Ready to push to GitHub!
echo.
echo NEXT STEPS:
echo 1. Create a new repository on GitHub: https://github.com/new
echo 2. Name it: cell-site-mapping
echo 3. Run these commands:
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/cell-site-mapping.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo ========================================
echo Then deploy:
echo - Frontend: https://vercel.com/
echo - Backend: https://railway.app/
echo ========================================
echo.
pause
