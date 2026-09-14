@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Push changes to GitHub
echo   Gokusan453/DISCORD  --  Vercel deploys itself
echo ============================================
echo.

git --version >nul 2>&1
if errorlevel 1 (
  echo [X] Git is not installed.
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

echo --- Staging files (.env is skipped) ---
git add .
git commit -m "Update bot" || echo (nothing changed)

echo.
echo --- Pushing ---
git push -u origin main

echo.
echo ============================================
echo  Done. Vercel starts a new deploy by itself.
echo  Give it about a minute.
echo ============================================
pause
