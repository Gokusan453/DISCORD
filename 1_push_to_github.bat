@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Wijzigingen naar GitHub pushen
echo   Gokusan453/DISCORD  ->  Vercel deployt zelf
echo ============================================
echo.

git --version >nul 2>&1
if errorlevel 1 (
  echo [X] Git is niet geinstalleerd.
  echo     Download: https://git-scm.com/download/win
  echo.
  pause
  exit /b 1
)

if not exist ".git" (
  git init
  git branch -M main
)

git remote remove origin >nul 2>&1
git remote add origin https://github.com/Gokusan453/DISCORD.git

echo --- Bestanden toevoegen (.env wordt overgeslagen) ---
git add .
git commit -m "Update bot" || echo (niets gewijzigd)

echo.
echo --- Pushen ---
git push -u origin main

echo.
echo ============================================
echo  Klaar. Vercel start automatisch een nieuwe
echo  deploy. Wacht ~1 minuut.
echo ============================================
pause
