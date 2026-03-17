"""
layer1_news.py — TradeIQ Layer 1: News Intelligence Pipeline
"""
import os
import sys
import json
import time
import argparse
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.layers.layer1_fetch import fetch_news
from backend.layers.layer1_sentiment import analyse_sentiment

DATA_DIR = str(ROOT / "backend" / "data")
INTEL_DIR = str(ROOT / "backend" / "data" / "company_intel")
REGIME_FILE = str(ROOT / "backend" / "data" / "regime_context.json")
WATCHLIST_FILE = str(ROOT / "backend" / "data" / "watchlist.json")
TENANT_ID = "0001"

DEFAULT_WATCHLIST = [
    {"ticker": "RELIANCE", "name": "Reliance Industries", "sector": "Energy"},
    {"ticker": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
    {"ticker": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking"},
    {"ticker": "INFY", "name": "Infosys", "sector": "IT"},
    {"ticker": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking"},
    {"ticker": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG"},
    {"ticker": "ITC", "name": "ITC Limited", "sector": "FMCG"},
    {"ticker": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    {"ticker": "BAJFINANCE", "name": "Bajaj Finance", "sector": "Banking"},
    {"ticker": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
    {"ticker": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking"},
    {"ticker": "LT", "name": "Larsen and Toubro", "sector": "Infra"},
    {"ticker": "ASIANPAINT", "name": "Asian Paints", "sector": "Chemicals"},
    {"ticker": "AXISBANK", "name": "Axis Bank", "sector": "Banking"},
    {"ticker": "MARUTI", "name": "Maruti Suzuki", "sector": "Auto"},
    {"ticker": "TITAN", "name": "Titan Company", "sector": "FMCG"},
    {"ticker": "WIPRO", "name": "Wipro", "sector": "IT"},
    {"ticker": "NESTLEIND", "name": "Nestle India", "sector": "FMCG"},
    {"ticker": "ULTRACEMCO", "name": "UltraTech Cement", "sector": "Infra"},
    {"ticker": "NTPC", "name": "NTPC Limited", "sector": "Energy"},
    {"ticker": "ONGC", "name": "Oil and Natural Gas Corp", "sector": "Energy"},
    {"ticker": "TECHM", "name": "Tech Mahindra", "sector": "IT"},
    {"ticker": "HCLTECH", "name": "HCL Technologies", "sector": "IT"},
    {"ticker": "SUNPHARMA", "name": "Sun Pharmaceutical", "sector": "Pharma"},
    {"ticker": "CIPLA", "name": "Cipla", "sector": "Pharma"},
    {"ticker": "DRREDDY", "name": "Dr Reddys Laboratories", "sector": "Pharma"},
    {"ticker": "BAJAJFINSV", "name": "Bajaj Finserv", "sector": "Banking"},
    {"ticker": "ADANIPORTS", "name": "Adani Ports and SEZ", "sector": "Infra"},
    {"ticker": "TATAMOTORS", "name": "Tata Motors", "sector": "Auto"},
    {"ticker": "TATASTEEL", "name": "Tata Steel", "sector": "Metals"},
    {"ticker": "JSWSTEEL", "name": "JSW Steel", "sector": "Metals"},
    {"ticker": "HINDALCO", "name": "Hindalco Industries", "sector": "Metals"},
    {"ticker": "COALINDIA", "name": "Coal India", "sector": "Energy"},
    {"ticker": "BRITANNIA", "name": "Britannia Industries", "sector": "FMCG"},
    {"ticker": "HEROMOTOCO", "name": "Hero MotoCorp", "sector": "Auto"},
    {"ticker": "EICHERMOT", "name": "Eicher Motors", "sector": "Auto"},
    {"ticker": "BPCL", "name": "Bharat Petroleum", "sector": "Energy"},
    {"ticker": "INDUSINDBK", "name": "IndusInd Bank", "sector": "Banking"},
    {"ticker": "APOLLOHOSP", "name": "Apollo Hospitals", "sector": "Pharma"},
    {"ticker": "TATACONSUM", "name": "Tata Consumer Products", "sector": "FMCG"},
    {"ticker": "SBILIFE", "name": "SBI Life Insurance", "sector": "Banking"},
    {"ticker": "HDFCLIFE", "name": "HDFC Life Insurance", "sector": "Banking"},
    {"ticker": "BAJAJ-AUTO", "name": "Bajaj Auto", "sector": "Auto"},
    {"ticker": "ZOMATO", "name": "Zomato", "sector": "IT"},
    {"ticker": "DMART", "name": "Avenue Supermarts DMart", "sector": "FMCG"},
    {"ticker": "IRCTC", "name": "Indian Railway Catering", "sector": "Infra"},
    {"ticker": "HAL", "name": "Hindustan Aeronautics", "sector": "Infra"},
    {"ticker": "TATAPOWER", "name": "Tata Power", "sector": "Energy"},
    {"ticker": "LUPIN", "name": "Lupin", "sector": "Pharma"},
    {"ticker": "DIVISLAB", "name": "Divis Laboratories", "sector": "Pharma"},
]


def _load_regime() -> dict:
    try:
        if os.path.exists(REGIME_FILE):
            with open(REGIME_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _load_watchlist() -> list:
    try:
        if os.path.exists(WATCHLIST_FILE):
            with open(WATCHLIST_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_WATCHLIST


def _save_intel(intel: dict, ticker: str) -> str:
    os.makedirs(INTEL_DIR, exist_ok=True)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"company_intel_{ticker}_{date_str}.json"
    filepath = os.path.join(INTEL_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(intel, f, indent=2)
    return filepath


def run_layer1_news(
    ticker: str,
    company_name: str,
    sector: str = "Unknown",
    tenant_id: str = TENANT_ID,
    max_articles: int = 8,
    verbose: bool = True,
) -> dict:
    if verbose:
        print(f"  [{ticker}] Fetching news...")

    regime = _load_regime()
    articles = fetch_news(ticker, company_name, max_articles=max_articles)

    if verbose:
        real_articles = [a for a in articles if a.get("fingerprint") != "placeholder"]
        print(f"  [{ticker}] Found {len(real_articles)} unique articles")

    if verbose:
        print(f"  [{ticker}] Analysing sentiment...")
    sentiment = analyse_sentiment(ticker, company_name, articles, regime)

    intel = {
        "ticker": ticker,
        "company_name": company_name,
        "sector_code": sector,
        "tenant_id": tenant_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "articles_fetched": len(articles),
        "long_catalysts": sentiment.get("long_catalysts", []),
        "short_catalysts": sentiment.get("short_catalysts", []),
        "net_sentiment_score": sentiment.get("net_sentiment_score", 0.0),
        "dominant_direction": sentiment.get("dominant_direction", "NEUTRAL"),
        "intraday_relevance": sentiment.get("intraday_relevance", "LOW"),
        "catalyst_summary": sentiment.get("catalyst_summary", ""),
        "raw_articles": [
            {
                "headline": a["headline"],
                "source": a["source"],
                "source_trust": a["source_trust"],
                "published_at": a["published_at"],
                "recency_weight": a["recency_weight"],
                "url": a["url"],
            }
            for a in articles
        ],
        "oi_data": {},
        "promoter_pledge_pct": 0.0,
        "fii_activity": "neutral",
        "earnings": {},
        "fundamentals": {},
    }

    filepath = _save_intel(intel, ticker)
    if verbose:
        print(f"  [{ticker}] Saved: {filepath}")
    return intel


def run_batch(
    n: int = 50,
    delay_seconds: float = 1.5,
    verbose: bool = True,
) -> dict:
    watchlist = _load_watchlist()[:n]
    total = len(watchlist)
    results = {"processed": 0, "errors": 0, "high_relevance": []}

    print("\nTradeIQ Layer 1 — News Intelligence Pipeline")
    print(f"Processing {total} companies...")
    print("=" * 60)

    for i, company in enumerate(watchlist, 1):
        ticker = company["ticker"]
        name = company["name"]
        sector = company.get("sector", "Unknown")

        bar_filled = int((i - 1) / total * 30)
        bar = "█" * bar_filled + "░" * (30 - bar_filled)
        print(f"\r[{bar}] {i}/{total} {ticker:<14}", end="", flush=True)

        try:
            intel = run_layer1_news(ticker, name, sector, verbose=False)
            results["processed"] += 1
            if intel.get("intraday_relevance") == "HIGH":
                results["high_relevance"].append({
                    "ticker": ticker,
                    "direction": intel["dominant_direction"],
                    "summary": intel["catalyst_summary"],
                })
        except Exception as e:
            results["errors"] += 1
            if verbose:
                print(f"\n  ERROR [{ticker}]: {e}")

        if i < total:
            time.sleep(delay_seconds)

    print(f"\r[{'█' * 30}] {total}/{total} Complete!        ")
    print("=" * 60)
    print(f"Processed: {results['processed']}  Errors: {results['errors']}")

    if results["high_relevance"]:
        print(f"\nHigh-Relevance Companies Today ({len(results['high_relevance'])}):")
        for item in results["high_relevance"]:
            print(f"  {item['ticker']:<14} {item['direction']:<8} {item['summary'][:60]}")

    print("=" * 60)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TradeIQ Layer 1 — News Intelligence Pipeline"
    )
    parser.add_argument("--ticker", type=str, default=None)
    parser.add_argument("--batch", type=int, default=None)
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(DEFAULT_WATCHLIST, f, indent=2)
        print(f"Created watchlist: {WATCHLIST_FILE}")

    if args.ticker:
        watchlist = _load_watchlist()
        match = next((c for c in watchlist if c["ticker"] == args.ticker.upper()), None)
        if match:
            ticker = match["ticker"]
            name = match["name"]
            sector = match.get("sector", "Unknown")
        else:
            ticker = args.ticker.upper()
            name = ticker
            sector = "Unknown"

        print(f"\nTradeIQ Layer 1 — {ticker}")
        print("=" * 60)
        intel = run_layer1_news(ticker, name, sector)
        print("\nINTELLIGENCE SUMMARY:")
        print(f"  Direction:   {intel['dominant_direction']}")
        print(f"  Relevance:   {intel['intraday_relevance']}")
        print(f"  Sentiment:   {intel['net_sentiment_score']:+.3f}")
        print(f"  Summary:     {intel['catalyst_summary']}")
    elif args.batch:
        run_batch(n=args.batch, delay_seconds=args.delay)
    else:
        print("Usage:")
        print("  python backend/layers/layer1_news.py --ticker RELIANCE")
        print("  python backend/layers/layer1_news.py --batch 10")
        print("  python backend/layers/layer1_news.py --batch 50 --delay 2")

