"""
regime.py — FastAPI endpoints for Layer 0 regime data
"""
import json
import os
import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/regime", tags=["regime"])

_ROOT = Path(__file__).resolve().parent.parent.parent
REGIME_FILE  = str(_ROOT / "backend" / "data" / "regime_context.json")
HISTORY_FILE = str(_ROOT / "backend" / "data" / "regime_history.json")

class RegimeRunRequest(BaseModel):
    date:     Optional[str]   = None
    mock_vix: Optional[float] = None

@router.get("/today")
async def get_today_regime():
    """
    Return today's regime context.
    Reads from cached file — fast, no external API calls.
    """
    if not os.path.exists(REGIME_FILE):
        raise HTTPException(
            status_code=404,
            detail="Regime not generated yet. Run layer0.py first."
        )
    with open(REGIME_FILE) as f:
        data = json.load(f)

    # Check if it's today's data
    today = datetime.date.today().strftime("%Y-%m-%d")
    if data.get("date") != today:
        data["warning"] = f"Regime data is from {data.get('date')} — not today"

    return data

@router.post("/run")
async def run_regime(request: RegimeRunRequest):
    """
    Trigger Layer 0 classification synchronously.
    Used by the validator and the scheduler.
    """
    try:
        import sys
        sys.path.insert(0, ".")
        from backend.layers.layer0 import classify_regime
        result = classify_regime(
            date_str=request.date,
            mock_vix=request.mock_vix
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_regime_history(days: int = 30):
    """
    Return regime history for the last N days.
    Used by the dashboard analytics panel.
    """
    if not os.path.exists(HISTORY_FILE):
        return {"history": [], "message": "No history yet"}
    with open(HISTORY_FILE) as f:
        history = json.load(f)
    return {"history": history[-days:], "total_days": len(history)}

@router.get("/stats")
async def get_regime_stats():
    """
    Return regime statistics — how many days of each type,
    hit rates, average VIX. Used by the analytics panel.
    """
    if not os.path.exists(HISTORY_FILE):
        return {"message": "No history yet"}
    with open(HISTORY_FILE) as f:
        history = json.load(f)

    total = len(history)
    if total == 0:
        return {"message": "No history yet"}

    counts = {}
    dnt_days  = 0
    vix_total = 0.0
    vix_count = 0

    for entry in history:
        regime = entry.get("regime", "UNKNOWN")
        counts[regime] = counts.get(regime, 0) + 1
        if entry.get("do_not_trade"):
            dnt_days += 1
        if entry.get("vix"):
            vix_total += entry["vix"]
            vix_count += 1

    return {
        "total_days":     total,
        "regime_counts":  counts,
        "dnt_days":       dnt_days,
        "dnt_pct":        round(dnt_days / total * 100, 1),
        "avg_vix":        round(vix_total / vix_count, 1) if vix_count else None,
        "trading_days":   total - dnt_days,
    }


@router.get("/warmup")
async def get_warmup_status():
    """
    Return warm-up gate status for Learn Mode.
    Used by dashboard Settings panel and Learn Mode gate.
    """
    try:
        import sys
        sys.path.insert(0, ".")
        from backend.layers.warm_up import get_warmup_status as _get_warmup_status
        return _get_warmup_status()
    except Exception as e:
        return {
            "observed_days": 0,
            "gate_unlocked": False,
            "days_remaining": 5,
            "required_days": 5,
            "pct_complete": 0,
            "error": str(e),
        }
