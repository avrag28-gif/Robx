@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python belum terpasang atau launcher py tidak ditemukan.
  echo Instal Python 3.10+ dari https://www.python.org/downloads/windows/
  echo Pastikan opsi Add Python to PATH diaktifkan.
  pause
  exit /b 1
)
py -3 app.py
if errorlevel 1 (
  echo Aplikasi berhenti kerana terjadi kesalahan.
  pause
)
endlocal
