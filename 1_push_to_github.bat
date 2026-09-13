@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Bot naar GitHub pushen (UATOLIFE/DISCORD)
echo ============================================
echo.

git --version >nul 2>&1
if errorlevel 1 (
  echo [X] Git is niet geinstalleerd.
  echo     Download: https://git-scm.com/download/win
  echo     Installeer, herstart je pc en dubbelklik dit bestand opnieuw.
  echo.
  pause
  exit /b 1
)

if not exist ".git" (
  git init
)

git config user.name  "UATOLIFE"
git config user.email "uatolife@users.noreply.github.com"

echo.
echo --- Bestanden toevoegen (.env wordt overgeslagen) ---
git add .
git commit -m "Discord bot" 2>nul || echo (niets nieuws om te committen)

git branch -M main

git remote remove origin >nul 2>&1
git remote add origin https://github.com/UATOLIFE/DISCORD.git

echo.
echo --- Pushen naar GitHub ---
echo Er kan een GitHub-inlogvenster openen. Log in en ga akkoord.
echo.
git push -u origin main

echo.
echo ============================================
echo  Klaar. Ververs je GitHub-pagina.
echo  Zie je .env in de lijst? STOP en zeg het me.
echo ============================================
pause
