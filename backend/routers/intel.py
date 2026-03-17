"""
intel.py — FastAPI endpoints for company intelligence data.
"""
import json
import os
import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/intel", tags=["intelligence"])

ROOT = Path(__file__).resolve().parent.parent.parent
INTEL_DIR = ROOT / "backend" / "data" / "company_intel"


class IntelRunRequest(BaseModel):
    ticker: str
    company_name: Optional[str] = None


@router.get("/{ticker}")
async def get_company_intel(ticker: str, date: Optional[str] = None):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    ticker = ticker.upper()
    filename = f"company_intel_{ticker}_{date}.json"
    filepath = INTEL_DIR / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No intelligence file for {ticker} on {date}. "
                f"Run: python backend/layers/layer1_news.py --ticker {ticker}"
            ),
        )
    with filepath.open() as f:
        return json.load(f)


@router.get("/")
async def list_available_intel(date: Optional[str] = None):
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    if not INTEL_DIR.exists():
        return {"date": date, "companies": [], "count": 0}

    files = os.listdir(INTEL_DIR)
    tickers = []
    for f in files:
        if date in f and f.endswith(".json"):
            ticker = f.replace("company_intel_", "").replace(f"_{date}.json", "")
            tickers.append(ticker)
    return {"date": date, "companies": sorted(tickers), "count": len(tickers)}


@router.post("/run")
async def run_intel(request: IntelRunRequest):
    try:
        import sys

        root = str(ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
        from backend.layers.layer1_news import run_layer1_news, _load_watchlist

        ticker = request.ticker.upper()
        name = request.company_name
        sector = "Unknown"

        if not name:
            watchlist = _load_watchlist()
            match = next((c for c in watchlist if c["ticker"] == ticker), None)
            if match:
                name = match["name"]
                sector = match.get("sector", "Unknown")
            else:
                name = ticker

        result = run_layer1_news(ticker, name, sector, verbose=False)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

