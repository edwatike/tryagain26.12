@echo off
echo Starting Chrome in CDP mode...
echo Chrome will be available at http://127.0.0.1:9222
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --headless --disable-gpu
echo Chrome started in background
echo You can check it at http://127.0.0.1:9222/json/version
pause

