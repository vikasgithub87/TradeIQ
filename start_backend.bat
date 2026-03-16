@echo off
cd /d C:\Users\m3n2c7\TradeIQ

echo Installing backend dependencies...
py -m pip install uvicorn fastapi python-dotenv sqlalchemy asyncpg pydantic --quiet

echo.
echo Starting TradeIQ backend on http://localhost:8000
echo Press Ctrl+C to stop.
echo.
py -m uvicorn backend.main:app --reload --port 8000

pause
