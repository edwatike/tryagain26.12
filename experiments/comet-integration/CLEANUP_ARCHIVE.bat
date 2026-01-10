@echo off
setlocal EnableExtensions

REM Safe cleanup: move experimental files into an archive folder (no deletion)
pushd "%~dp0"

for /f "tokens=1-4 delims=/. " %%a in ("%date%") do set YYYYMMDD=%%d%%b%%c
for /f "tokens=1-3 delims=:., " %%a in ("%time%") do set HHMMSS=%%a%%b%%c
set ARCHIVE_DIR=_archive\%YYYYMMDD%_%HHMMSS%

echo Creating archive folder: %ARCHIVE_DIR%
mkdir "%ARCHIVE_DIR%" 2>nul

REM Keep these files in place:
REM - README.md
REM - requirements.txt
REM - START_HERE.bat
REM - test_single_domain.py
REM - domains.txt

REM Move noisy artifacts
if exist *.log move /Y *.log "%ARCHIVE_DIR%" >nul
if exist *.csv move /Y *.csv "%ARCHIVE_DIR%" >nul
if exist *.json move /Y *.json "%ARCHIVE_DIR%" >nul
if exist screenshot_*.png move /Y screenshot_*.png "%ARCHIVE_DIR%" >nul

REM Move old batch runners (except START_HERE.bat)
for %%f in (run_*.bat) do (
  if /I not "%%f"=="START_HERE.bat" move /Y "%%f" "%ARCHIVE_DIR%" >nul
)

REM Move extra python scripts (keep test_single_domain.py)
for %%f in (*.py) do (
  if /I not "%%f"=="test_single_domain.py" move /Y "%%f" "%ARCHIVE_DIR%" >nul
)

REM Move folders with experiments (if any)
for %%d in (src tests data logs) do (
  if exist "%%d" (
    move /Y "%%d" "%ARCHIVE_DIR%" >nul
  )
)

echo.
echo Cleanup completed.
echo Archived items are in: %ARCHIVE_DIR%
echo.
pause

popd
endlocal
