@echo off
setlocal

REM Always run from this folder
pushd "%~dp0"

echo ===============================================
echo Comet Integration Extractor
echo ===============================================
echo.
echo Requirements:
echo - Comet must be running with CDP on 127.0.0.1:9222
echo - Do NOT touch mouse/keyboard during the run
echo.

REM Create venv if missing
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment .venv ...
  py -3 -m venv .venv 2>nul || python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Running test_single_domain.py ...
echo.
python test_single_domain.py

echo.
echo Done. Artifacts are in cdp_debug\
echo.
pause

popd
endlocal
