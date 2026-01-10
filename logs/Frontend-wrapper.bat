@echo off
cd /d d:\tryagain\scripts\..\frontend\moderator-dashboard-ui
echo [Frontend] Starting...
if not exist node_modules (
    echo [Frontend] Installing dependencies...
    call npm install
)
echo [Frontend] Starting Next.js on port 3000...
set NODE_OPTIONS=--max-old-space-size=4096
npm run dev