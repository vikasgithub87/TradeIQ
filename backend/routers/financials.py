"""
financials.py — FastAPI endpoints for financial data.
"""
import json
import os
import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/financials", tags=["financials"])

ROOT = Path(__file__).resolve().parent.parent.parent
INTEL_DIR = ROOT / "backend" / "data" / "company_intel"


@router.get("/{ticker}")
async def get_financial_data(ticker: str, date: Optional[str] = None):
    """Return financial section of company intel file."""
    if not date:
        date = datetime.date.today().strftime("%Y-%m-%d")
    ticker = ticker.upper()
    filename = f"company_intel_{ticker}_{date}.json"
    filepath = INTEL_DIR / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"No data for {ticker} on {date}. "
                f"Run: python backend/layers/layer1_merge.py --ticker {ticker}"
            ),
        )
    with filepath.open() as f:
        intel = json.load(f)
    return {
        "ticker": intel.get("ticker"),
        "date": intel.get("date"),
        "current_price": intel.get("current_price"),
        "market_cap_cr": intel.get("market_cap_cr"),
        "pe_ratio": intel.get("pe_ratio"),
        "fii_activity": intel.get("fii_activity"),
        "promoter_pledge_pct": intel.get("promoter_pledge_pct"),
        "near_52w_high": intel.get("near_52w_high"),
        "near_52w_low": intel.get("near_52w_low"),
        "pcr": intel.get("pcr"),
        "oi_signal": intel.get("oi_signal"),
        "eps_surprise_pct": intel.get("eps_surprise_pct"),
        "surprise_label": intel.get("surprise_label"),
        "in_results_window": intel.get("in_results_window"),
        "fundamentals": intel.get("fundamentals", {}),
        "earnings": intel.get("earnings", {}),
        "data_quality": intel.get("data_quality", {}),
    }


@router.post("/run/{ticker}")
async def run_financial_merge(ticker: str):
    """Trigger financial data merge for a company."""
    try:
        import sys

        root = str(ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
        from backend.layers.layer1_merge import merge_financial_data

        result = merge_financial_data(ticker.upper(), verbose=False)
        return {
            "ticker": result.get("ticker"),
            "price": result.get("current_price"),
            "pcr": result.get("pcr"),
            "signal": result.get("oi_signal"),
            "quality": result.get("data_quality", {}).get(
                "overall_confidence"
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

