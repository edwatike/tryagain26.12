@echo off
cd /d %~dp0frontend\moderator-dashboard-ui
echo [Frontend] Starting...
if not exist node_modules (
    echo [Frontend] Installing dependencies...
    call npm install
)
echo [Frontend] Starting Next.js on port 3000...
npm run dev
pause
