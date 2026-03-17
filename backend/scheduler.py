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
    # Layer 1 — full batch at 08:00 IST every weekday
    "run-layer1-morning": {
        "task":     "backend.scheduler.task_run_layer1_batch",
        "schedule": crontab(hour=8, minute=0,
                            day_of_week="mon,tue,wed,thu,fri"),
    },
    # Layer 1 — refresh during market hours every 15 minutes
    "run-layer1-intraday": {
        "task":     "backend.scheduler.task_run_layer1_batch",
        "schedule": crontab(minute="*/15",
                            hour="9,10,11,12,13,14,15",
                            day_of_week="mon,tue,wed,thu,fri"),
    },
    # Layer 1 financials — runs at 08:30 IST after news pipeline
    "run-layer1-financials-morning": {
        "task":     "backend.scheduler.task_run_layer1_financials",
        "schedule": crontab(hour=8, minute=30,
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


@app.task(name="backend.scheduler.task_run_layer1_batch")
def task_run_layer1_batch():
    """Celery task — runs Layer 1 for top 20 companies."""
    from pathlib import Path
    _root = str(Path(__file__).resolve().parent.parent)
    if _root not in sys.path:
        sys.path.insert(0, _root)
    try:
        from backend.layers.layer1_news import run_batch
        result = run_batch(n=20, delay_seconds=1.0, verbose=False)
        return {"status": "ok", "processed": result.get("processed", 0)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.task(name="backend.scheduler.task_run_layer1_financials")
def task_run_layer1_financials():
    """Celery task — merges financial data for top 20 companies."""
    sys.path.insert(0, ".")
    try:
        from backend.layers.layer1_merge import merge_financial_data
        from backend.layers.layer1_news import _load_watchlist

        watchlist = _load_watchlist()[:20]
        processed = 0
        for company in watchlist:
            try:
                merge_financial_data(company["ticker"], verbose=False)
                processed += 1
                import time
                time.sleep(1.0)
            except Exception:
                continue
        return {"status": "ok", "processed": processed}
    except Exception as e:
        return {"status": "error", "message": str(e)}
