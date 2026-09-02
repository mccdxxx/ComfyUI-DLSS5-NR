@echo off
setlocal
echo [DLSS5-NR] Developer build v0.3.0-alpha2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0native\build_native.ps1"
if errorlevel 1 (
  echo.
  echo [DLSS5-NR] BUILD FAILED.
  exit /b 1
)
echo.
echo [DLSS5-NR] Native build finished successfully.
