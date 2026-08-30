@echo off
echo Starting FinShield Services...

echo Starting FastAPI Backend (with embedded Frontend on port 8000)...
start "FinShield API" cmd /k ".\.venv\Scripts\activate && python scripts/run_api.py"

echo Starting ngrok tunnel on port 8000 with static domain...
start "ngrok" cmd /k "ngrok http --domain=imprudent-tranquil-precise.ngrok-free.dev 8000"

echo.
echo ===================================================
echo FinShield is running!
echo.
echo Local Dashboard: http://localhost:8000
echo.
echo Your Omi Webhook URL is configured as:
echo https://imprudent-tranquil-precise.ngrok-free.dev/api/v1/omi/webhook
echo ===================================================
echo.
pause
