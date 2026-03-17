"""
layer1_merge.py — Merges news intelligence with financial data.
"""
import os
import sys
import json
import datetime
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.layers.layer1_financials import run_layer1_financials  # noqa: E402
from backend.layers.layer1_earnings import (  # noqa: E402
    fetch_earnings_data,
    fetch_promoter_data,
)
from backend.layers.layer1_oi import fetch_oi_data  # noqa: E402

INTEL_DIR = ROOT / "backend" / "data" / "company_intel"
TENANT_ID = "0001"


def merge_financial_data(
    ticker: str,
    tenant_id: str = TENANT_ID,
    verbose: bool = True,
) -> dict:
    """
    Load existing company_intel file and enrich with financial data.
    """
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"company_intel_{ticker}_{date_str}.json"
    filepath = INTEL_DIR / filename

    if filepath.exists():
        with filepath.open() as f:
            intel = json.load(f)
        if verbose:
            print(f"  [{ticker}] Loaded existing intel file")
    else:
        intel = {
            "ticker": ticker,
            "company_name": ticker,
            "tenant_id": tenant_id,
            "date": date_str,
            "timestamp": datetime.datetime.now().isoformat(),
            "long_catalysts": [],
            "short_catalysts": [],
            "net_sentiment_score": 0.0,
            "dominant_direction": "NEUTRAL",
            "intraday_relevance": "LOW",
            "catalyst_summary": "",
        }
        if verbose:
            print(f"  [{ticker}] No news intel found — creating base file")

    if verbose:
        print(f"  [{ticker}] Fetching price and fundamentals...")
    financials = run_layer1_financials(ticker, tenant_id, verbose=False)

    if verbose:
        print(f"  [{ticker}] Fetching earnings data...")
    earnings = fetch_earnings_data(ticker)

    if verbose:
        print(f"  [{ticker}] Fetching promoter data...")
    promoter = fetch_promoter_data(ticker)

    if verbose:
        print(f"  [{ticker}] Fetching F&O OI data...")
    oi_data = fetch_oi_data(ticker)

    intel["ohlcv"] = financials.get("ohlcv", {})
    intel["fundamentals"] = financials.get("fundamentals", {})
    intel["fii_dii"] = financials.get("fii_dii", {})
    intel["peer_comparison"] = financials.get("peer_comparison", {})
    intel["earnings"] = earnings
    intel["promoter"] = promoter
    intel["oi_data"] = oi_data

    intel["current_price"] = financials.get("current_price")
    intel["market_cap_cr"] = financials.get("market_cap_cr")
    intel["pe_ratio"] = financials.get("pe_ratio")
    intel["fii_activity"] = financials.get("fii_activity", "neutral")
    intel["promoter_pledge_pct"] = promoter.get("promoter_pledge_pct", 0.0)
    intel["near_52w_high"] = financials.get("near_52w_high", False)
    intel["near_52w_low"] = financials.get("near_52w_low", False)
    intel["pcr"] = oi_data.get("pcr", 1.0)
    intel["oi_signal"] = oi_data.get("oi_signal", "neutral")
    intel["eps_surprise_pct"] = earnings.get("eps_surprise_pct")
    intel["surprise_label"] = earnings.get("surprise_label")
    intel["in_results_window"] = earnings.get("in_results_window", False)
    intel["results_expected"] = earnings.get("results_expected", False)

    intel["data_quality"] = {
        "ohlcv_confidence": financials.get("ohlcv", {}).get("confidence", 0),
        "fundamentals_confidence": financials.get("fundamentals", {}).get(
            "confidence", 0
        ),
        "earnings_confidence": earnings.get("confidence", 0),
        "oi_confidence": oi_data.get("confidence", 0),
    }
    overall = (
        intel["data_quality"]["ohlcv_confidence"]
        + intel["data_quality"]["fundamentals_confidence"]
        + intel["data_quality"]["earnings_confidence"]
    ) / 3
    intel["data_quality"]["overall_confidence"] = round(overall, 2)
    intel["data_quality"]["last_updated"] = datetime.datetime.now().isoformat()

    INTEL_DIR.mkdir(parents=True, exist_ok=True)
    with filepath.open("w") as f:
        json.dump(intel, f, indent=2)

    if verbose:
        print(f"  [{ticker}] Saved enriched intel: {filepath}")

    return intel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TradeIQ Layer 1 — Financial Data Merge"
    )
    parser.add_argument("--ticker", type=str, default="RELIANCE")
    args = parser.parse_args()

    t = args.ticker.upper()
    print(f"\nTradeIQ Layer 1 Merge — {t}")
    print("=" * 60)
    intel = merge_financial_data(t)

    print("\nEnriched Intel Summary:")
    print(f"  Price:          ₹{intel.get('current_price', 'N/A')}")
    print(f"  Market cap:     ₹{intel.get('market_cap_cr', 'N/A')} Cr")
    print(f"  P/E ratio:      {intel.get('pe_ratio', 'N/A')}")
    print(f"  PCR:            {intel.get('pcr', 'N/A')}")
    print(f"  OI signal:      {intel.get('oi_signal', 'N/A')}")
    print(f"  FII activity:   {intel.get('fii_activity', 'N/A')}")
    print(f"  Near 52W high:  {intel.get('near_52w_high', False)}")
    print(f"  Near 52W low:   {intel.get('near_52w_low', False)}")
    print(f"  Pledge pct:     {intel.get('promoter_pledge_pct', 0)}%")
    if intel.get("eps_surprise_pct") is not None:
        print(
            f"  EPS surprise:   {intel['eps_surprise_pct']:+.1f}% "
            f"({intel.get('surprise_label', '')})"
        )
    conf = intel.get("data_quality", {}).get("overall_confidence", 0)
    print(f"  Data quality:   {int(conf * 100)}% confidence")

