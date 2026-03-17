"""
scheduler.py — Celery task scheduler for TradeIQ
Runs Layer 0 at 07:30 IST every weekday morning.

To start the scheduler on Windows:
    celery -A backend.scheduler worker --loglevel=info --pool=solo
    celery -A backend.scheduler beat --loglevel=info

Requires Redis running locally:
    Download from: https://github.com/tporadowski/redis/releases
    Run: redis-server
"""
import os
import sys
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# Redis connection — default local Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("tradeiq", broker=REDIS_URL, backend=REDIS_URL)

app.conf.timezone = "Asia/Kolkata"
app.conf.enable_utc = True

app.conf.beat_schedule = {
    # Layer 0 — runs at 07:30 IST every weekday (Mon-Fri)
    "run-layer0-morning": {
        "task":     "backend.scheduler.task_run_layer0",
        "schedule": crontab(hour=7, minute=30,
                            day_of_week="mon,tue,wed,thu,fri"),
    },
}

@app.task(name="backend.scheduler.task_run_layer0")
def task_run_layer0():
    """Celery task — runs Layer 0 market regime classification."""
    from pathlib import Path
    _root = str(Path(__file__).resolve().parent.parent)  # backend/ -> project root
    if _root not in sys.path:
        sys.path.insert(0, _root)
    try:
        from backend.layers.layer0 import classify_regime
        result = classify_regime()
        return {"status": "ok", "regime": result.get("regime")}
    except Exception as e:
        return {"status": "error", "message": str(e)}
