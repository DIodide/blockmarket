@echo off
REM BlockMarket Stop All Services Script (Windows)
REM Closes all terminals and servers opened by start-all.bat

echo 🛑 Stopping BlockMarket Services...

REM Kill ngrok processes
echo Stopping ngrok...
taskkill /f /im ngrok.exe 2>nul
if %errorlevel% equ 0 (
    echo ✅ ngrok stopped
) else (
    echo ⚠️  ngrok was not running
)

REM Kill Node.js processes (Express server and Frontend)
echo Stopping Node.js servers...
taskkill /f /im node.exe 2>nul
if %errorlevel% equ 0 (
    echo ✅ Node.js servers stopped
) else (
    echo ⚠️  No Node.js servers were running
)

REM Kill Python processes
echo Stopping Python app...
taskkill /f /im python.exe 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python app stopped
) else (
    echo ⚠️  Python app was not running
)

REM Kill any remaining cmd processes that might be running our services
echo Cleaning up command windows...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq cmd.exe" /fo csv ^| findstr /v "Image Name"') do (
    set "pid=%%i"
    set "pid=!pid:"=!"
    taskkill /f /pid !pid! 2>nul
)

REM Kill processes on specific ports
echo Stopping services on ports...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":4040"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080"') do taskkill /f /pid %%a 2>nul

echo ✅ All BlockMarket services stopped!
echo.
echo Services that were stopped:
echo   - ngrok (port 4040)
echo   - Express server (port 3001)
echo   - Frontend (port 3000)
echo   - Python app (port 8080)
echo   - Mineflayer server
echo   - All related command windows

pause
