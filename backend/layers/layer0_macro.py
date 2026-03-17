"""
layer0_macro.py — Global macro morning snapshot for Layer 0
Fetches: SGX Nifty direction, US futures, Crude oil, Dollar Index.
These 4 numbers shape intraday sentiment before NSE opens.
"""
import os
import json
import datetime
import requests
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = str(_ROOT / "backend" / "data" / "macro_cache.json")

def fetch_crude_oil() -> Optional[float]:
    """
    Fetch Brent crude oil price using Yahoo Finance API.
    Returns price in USD per barrel or None on failure.
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(float(price), 2)
    except Exception:
        return None

def fetch_dollar_index() -> Optional[float]:
    """
    Fetch DXY (US Dollar Index) price using Yahoo Finance API.
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(float(price), 2)
    except Exception:
        return None

def fetch_sp500_futures() -> Optional[dict]:
    """
    Fetch S&P 500 futures (ES=F) to gauge US market overnight direction.
    Returns price and change percentage.
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/ES=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        meta   = data["chart"]["result"][0]["meta"]
        price  = round(float(meta["regularMarketPrice"]), 2)
        prev   = round(float(meta["chartPreviousClose"]), 2)
        change = round(((price - prev) / prev) * 100, 2) if prev else 0.0
        return {"price": price, "change_pct": change,
                "direction": "positive" if change > 0 else "negative" if change < 0 else "flat"}
    except Exception:
        return None

def fetch_india_vix(mock_vix: Optional[float] = None) -> float:
    """
    Fetch India VIX from NSE.
    Falls back to cache, then to 15.0 (historical average).
    If mock_vix provided (for testing), return it directly.
    """
    if mock_vix is not None:
        return mock_vix

    # Try NSE API
    try:
        url     = "https://www.nseindia.com/api/allIndices"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
            "Referer": "https://www.nseindia.com",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        for item in data.get("data", []):
            if item.get("index") == "INDIA VIX":
                vix = round(float(item["last"]), 2)
                _save_vix_cache(vix)
                return vix
    except Exception:
        pass

    # Try cache
    cached = _load_vix_cache()
    if cached:
        print(f"  VIX: using cached value {cached}")
        return cached

    # Final fallback
    print("  VIX: using default 15.0")
    return 15.0

def _save_vix_cache(vix: float):
    """Save VIX to cache file with timestamp."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        cache = _load_raw_cache()
        cache["vix"] = {"value": vix,
                        "date": datetime.date.today().strftime("%Y-%m-%d")}
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def _load_vix_cache() -> Optional[float]:
    """Load VIX from cache if it is from today or yesterday."""
    try:
        cache = _load_raw_cache()
        if "vix" not in cache:
            return None
        cached_date = datetime.date.fromisoformat(cache["vix"]["date"])
        today = datetime.date.today()
        if (today - cached_date).days <= 1:
            return cache["vix"]["value"]
    except Exception:
        pass
    return None

def _load_raw_cache() -> dict:
    """Load the raw cache JSON file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def get_macro_snapshot(mock_vix: Optional[float] = None) -> dict:
    """
    Fetch all macro data and return a combined snapshot.
    Safe — all individual fetches have try/except fallbacks.
    """
    print("  Fetching India VIX...")
    vix     = fetch_india_vix(mock_vix)

    print("  Fetching crude oil price...")
    crude   = fetch_crude_oil()

    print("  Fetching Dollar Index...")
    dxy     = fetch_dollar_index()

    print("  Fetching S&P 500 futures...")
    sp500   = fetch_sp500_futures()

    # Determine global sentiment
    bullish_signals = 0
    bearish_signals = 0
    if sp500 and sp500["change_pct"] > 0.3:
        bullish_signals += 1
    elif sp500 and sp500["change_pct"] < -0.3:
        bearish_signals += 1
    if crude and crude > 90:
        bearish_signals += 1  # High crude = inflation risk for India
    if dxy and dxy > 106:
        bearish_signals += 1  # Strong dollar = FII outflow risk

    global_sentiment = (
        "positive" if bullish_signals > bearish_signals
        else "negative" if bearish_signals > bullish_signals
        else "neutral"
    )

    return {
        "india_vix":        vix,
        "crude_oil_usd":    crude,
        "dollar_index":     dxy,
        "sp500_futures":    sp500,
        "global_sentiment": global_sentiment,
        "macro_fetched_at": datetime.datetime.now().isoformat(),
    }
