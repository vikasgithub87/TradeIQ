"""
scores.py — FastAPI endpoints for Layer 2 trading scores.
"""
import json
import os
import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/scores", tags=["scores"])

SCORES_DIR = "backend/data/scores"


@router.get("/today")
async def get_today_scores(limit: int = 10):
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    fp = os.path.join(SCORES_DIR, f"trading_scores_{date_str}.json")
    if not os.path.exists(fp):
        raise HTTPException(
            status_code=404,
            detail="Scores not generated yet. "
                   "Run: python backend/layers/layer2_runner.py",
        )
    with open(fp) as f:
        data = json.load(f)

    if "short_scores" in data:
        short_sorted = list(data.get("short_scores") or [])[:limit]
    else:
        all_scores = data.get("all_scores", [])
        th = data.get("threshold", 0)
        short_sorted = sorted(
            [
                s
                for s in all_scores
                if s.get("short_score", 0) >= th
                and "LOW_LIQUIDITY" not in s.get("short_flags", [])
            ],
            key=lambda x: x["short_score"],
            reverse=True,
        )[:limit]

    return {
        "date": data.get("date"),
        "regime": data.get("regime"),
        "threshold": data.get("threshold"),
        "total_companies": data.get("total_companies"),
        "above_threshold": data.get("above_threshold"),
        "top_scores": data.get("company_scores", [])[:limit],
        "short_scores": short_sorted,
        "theme_scores": data.get("theme_scores", [])[:5],
        "rotation_alerts": data.get("rotation_alerts", []),
        "breakout_stocks": data.get("breakout_stocks", []),
        "generated_at": data.get("generated_at"),
    }


@router.get("/company/{ticker}")
async def get_company_score(ticker: str, date: Optional[str] = None):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    fp = os.path.join(SCORES_DIR, f"trading_scores_{date}.json")
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail=f"No scores for {date}")
    with open(fp) as f:
        data = json.load(f)
    ticker = ticker.upper()
    match = next((s for s in data.get("all_scores", []) if s.get("ticker") == ticker), None)
    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"{ticker} not found in scores for {date}",
        )
    return match


@router.post("/run")
async def run_scores(
    date: Optional[str] = None,
    ignore_regime: bool = False,
    threshold: Optional[int] = None,
):
    """
    Run Layer 2 in a worker thread so asyncio.run(save_scores_to_db) inside
    run_layer2 does not conflict with FastAPI's running event loop.
    """
    try:
        import sys
        sys.path.insert(0, ".")
        from backend.layers.layer2_runner import run_layer2

        def _run() -> dict:
            return run_layer2(
                date_str=date,
                save_to_db=True,
                verbose=False,
                ignore_regime=ignore_regime,
                override_threshold=threshold,
            )

        result = await run_in_threadpool(_run)
        eff_threshold = result.get("threshold")
        return {
            "status": "ok",
            "date": result.get("date"),
            "scored": result.get("total_companies", 0),
            "above_threshold": result.get("above_threshold", 0),
            "short_above": len(result.get("short_scores", [])),
            "rotation_alerts": len(result.get("rotation_alerts", [])),
            "threshold": eff_threshold,
            "ignore_regime": ignore_regime,
            "message": (
                f"Scoring complete. Threshold {eff_threshold}"
                + (" (DO NOT TRADE overridden)." if ignore_regime else ".")
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/themes")
async def get_theme_scores(date: Optional[str] = None):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    fp = os.path.join(SCORES_DIR, f"trading_scores_{date}.json")
    if not os.path.exists(fp):
        raise HTTPException(status_code=404, detail=f"No scores for {date}")
    with open(fp) as f:
        data = json.load(f)
    return {"date": date, "theme_scores": data.get("theme_scores", [])}


@router.get("/shorts")
async def get_short_scores(date: Optional[str] = None, limit: int = 10):
    """
    Return today's top SHORT signals.
    Sorted by short_score descending.
    """
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    filepath = os.path.join(SCORES_DIR, f"trading_scores_{date}.json")
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Scores not generated yet. Run Layer 2 first.",
        )
    with open(filepath) as f:
        data = json.load(f)

    short_scores = data.get("short_scores", [])

    if not short_scores:
        all_scores = data.get("all_scores", [])
        threshold = data.get("threshold", 50)
        short_scores = sorted(
            [s for s in all_scores if s.get("short_score", 0) >= threshold],
            key=lambda x: x["short_score"],
            reverse=True,
        )

    return {
        "date": date,
        "regime": data.get("regime"),
        "short_scores": short_scores[:limit],
        "total_shorts": len(short_scores),
    }

