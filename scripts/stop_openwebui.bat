@echo off
REM Stop Kor'tana with Open WebUI (Windows)

echo Stopping Open WebUI and Kor'tana...

REM Stop Docker containers
docker compose -f docker-compose.openwebui.yml down

REM Find and stop backend (this will close the backend window)
taskkill /FI "WINDOWTITLE eq Kor'tana Backend*" /F > nul 2>&1

echo All services stopped
pause
