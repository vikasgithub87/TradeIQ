"""
signals.py — FastAPI endpoints for Layer 3 validated signals.
"""
import json
import os
import datetime
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/signals", tags=["signals"])

SIGNALS_DIR = "backend/data/signals"


@router.get("/today")
async def get_today_signals(limit: int = 10):
    """Return today's validated signals sorted by confidence."""
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filepath = os.path.join(SIGNALS_DIR, f"validated_signals_{date_str}.json")
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Signals not generated yet. Run: python backend/layers/layer3_runner.py",
        )
    with open(filepath) as f:
        data = json.load(f)
    return {
        "date": data.get("date"),
        "regime": data.get("regime"),
        "total_validated": data.get("total_validated"),
        "buy_signals": (data.get("buy_signals") or [])[:limit],
        "short_signals": (data.get("short_signals") or [])[:limit],
        "high_conviction": data.get("high_conviction", []),
        # Include all signals (including AVOID) so the UI can sort by confidence
        "all_signals": (data.get("all_signals") or [])[:max(limit * 5, 50)],
    }


@router.get("/company/{ticker}")
async def get_company_signal(ticker: str, date: Optional[str] = None):
    """Return validated signal for a specific company."""
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    filepath = os.path.join(SIGNALS_DIR, f"validated_signals_{date}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"No signals for {date}")
    with open(filepath) as f:
        data = json.load(f)
    ticker = ticker.upper()
    match = next((s for s in data.get("all_signals", []) if s.get("ticker") == ticker), None)
    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"{ticker} not found in validated signals for {date}",
        )
    return match


@router.post("/run")
async def run_signals(ticker: Optional[str] = None, date: Optional[str] = None):
    """Trigger Layer 3 validation."""
    try:
        import sys

        sys.path.insert(0, ".")
        from backend.layers.layer3_runner import run_layer3

        result = run_layer3(date_str=date, ticker=ticker, save_to_db=True, verbose=False)
        return {
            "status": "ok",
            "total_validated": result.get("total_validated", 0),
            "buy_signals": len(result.get("buy_signals", [])),
            "short_signals": len(result.get("short_signals", [])),
            "high_conviction": len(result.get("high_conviction", [])),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

