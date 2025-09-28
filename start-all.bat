@echo off
REM BlockMarket Start All Services Script (Windows)
REM Simple bare-bones script to start all services in separate command windows

echo 🚀 Starting BlockMarket Services...

REM Start ngrok
echo Starting ngrok...
start "ngrok" cmd /k "ngrok http 3001"

REM Start Express server
echo Starting Express server...
start "Express Server" cmd /k "cd /d bm-express-controller\master-server && npm run dev"
REM Starting Mineflayer server
echo Starting Mineflayer server...
start "Mineflayer Server" cmd /k "cd /d bm-mineflayer-controller && node socketReceiveNoQueue.js"

REM Start Frontend
echo Starting Frontend...
start "Frontend" cmd /k "cd /d bm-express-controller\frontend && npm run dev"

REM Start Python unified app
echo Starting Python unified app...
start "Python App" cmd /k "cd /d rl && python main.py --mode unified"

echo ✅ All services started in separate command windows!
echo Services:
echo   - ngrok: http://localhost:4040 (tunnel to 3001)
echo   - Express: http://localhost:3001
echo   - Frontend: http://localhost:3000
echo   - Python: http://localhost:8080

pause
