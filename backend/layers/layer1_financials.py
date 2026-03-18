"""
layer1_financials.py — Fetches financial data for NSE companies.
Uses yfinance with .NS suffix for NSE-listed stocks.
All fetches have try/except with graceful fallbacks.
Data freshness tracked with fetched_at timestamps.
"""
import os
import json
import datetime
import time
from typing import Optional, Dict, Any
from pathlib import Path

import pandas as pd  # noqa: F401  (used by yfinance history)

try:
    import yfinance as yf
except ImportError:
    raise ImportError(
        "yfinance not installed. Run: pip install yfinance pandas numpy"
    )

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "backend" / "data"

SECTOR_PEERS = {
    "RELIANCE": ["ONGC", "BPCL", "IOC"],
    "TCS": ["INFY", "WIPRO", "HCLTECH"],
    "HDFCBANK": ["ICICIBANK", "AXISBANK", "KOTAKBANK"],
    "INFY": ["TCS", "WIPRO", "HCLTECH"],
    "ICICIBANK": ["HDFCBANK", "AXISBANK", "SBIN"],
    "SBIN": ["ICICIBANK", "HDFCBANK", "BANKBARODA"],
    "TMPV": ["MARUTI", "M&M", "HYUNDAI"],
    "TMCV": ["ASHOKLEY", "EICHERMOT", "M&M"],
    "SUNPHARMA": ["CIPLA", "DRREDDY", "LUPIN"],
    "TATASTEEL": ["JSWSTEEL", "SAIL", "HINDALCO"],
    "WIPRO": ["TCS", "INFY", "HCLTECH"],
    "BHARTIARTL": ["IDEA", "TATACOMM", "HFCL"],
    "MARUTI": ["TATAMOTORS", "M&M", "HEROMOTOCO"],
    "ITC": ["HINDUNILVR", "BRITANNIA", "DABUR"],
    "BAJFINANCE": ["BAJAJFINSV", "CHOLAFIN", "MUTHOOTFIN"],
    "NTPC": ["TATAPOWER", "POWERGRID", "ADANIGREEN"],
}


def get_nse_ticker(ticker: str) -> str:
    """Convert NSE ticker to yfinance format by appending .NS."""
    # Handle demerged tickers — TATAMOTORS no longer exists
    DEMERGED_MAP = {
        "TATAMOTORS": "TMPV",  # Default to PV entity
    }
    ticker = DEMERGED_MAP.get(ticker, ticker)

    ticker = ticker.upper().strip()
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        return ticker + ".NS"
    return ticker


def fetch_intraday_ohlcv(
    ticker: str,
    interval: str = "5m",
    period: str = "1d",
) -> Dict[str, Any]:
    """
    Fetch intraday OHLCV data from yfinance.
    Returns dict with candles list and metadata.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "interval": interval,
        "candles": [],
        "current_price": None,
        "open_price": None,
        "day_high": None,
        "day_low": None,
        "volume": None,
        "vwap": None,
        "confidence": 0.0,
        "fetched_at": datetime.datetime.now().isoformat(),
        "error": None,
    }

    try:
        yf_ticker = get_nse_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            result["error"] = f"No intraday data returned for {ticker}"
            return result

        candles = []
        for ts, row in hist.iterrows():
            candles.append({
                "time": ts.isoformat(),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        if not candles:
            result["error"] = "Empty candles after processing"
            return result

        last_candle = candles[-1]

        try:
            typical_prices = [(c["high"] + c["low"] + c["close"]) / 3 for c in candles]
            volumes = [c["volume"] for c in candles]
            total_vol = sum(volumes)
            vwap = (
                sum(tp * v for tp, v in zip(typical_prices, volumes)) / total_vol
                if total_vol > 0 else None
            )
        except Exception:
            vwap = None

        try:
            last_time = datetime.datetime.fromisoformat(
                candles[-1]["time"].replace("Z", "+00:00")
            )
            age_hours = (
                datetime.datetime.now(datetime.timezone.utc) - last_time
            ).total_seconds() / 3600
            confidence = 1.0 if age_hours < 1 else (
                0.8 if age_hours < 4 else 0.6 if age_hours < 12 else 0.3
            )
        except Exception:
            confidence = 0.7

        result.update({
            "candles": candles,
            "current_price": last_candle["close"],
            "open_price": candles[0]["open"],
            "day_high": max(c["high"] for c in candles),
            "day_low": min(c["low"] for c in candles),
            "volume": sum(c["volume"] for c in candles),
            "vwap": round(vwap, 2) if vwap else None,
            "candle_count": len(candles),
            "confidence": round(confidence, 2),
        })
    except Exception as e:
        result["error"] = str(e)
        result["confidence"] = 0.0

    return result


def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch company fundamentals from yfinance.
    Includes P/E, market cap, 52W levels and proximity flags.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "market_cap_cr": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "debt_to_equity": None,
        "roe_pct": None,
        "revenue_growth_pct": None,
        "week52_high": None,
        "week52_low": None,
        "week52_high_pct": None,
        "week52_low_pct": None,
        "near_52w_high": False,
        "near_52w_low": False,
        "avg_volume_10d": None,
        "beta": None,
        "confidence": 0.0,
        "fetched_at": datetime.datetime.now().isoformat(),
        "error": None,
    }

    try:
        yf_ticker = get_nse_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            result["error"] = f"No fundamental data for {ticker}"
            return result

        current_price = info.get("regularMarketPrice") or info.get("currentPrice")
        week52_high = info.get("fiftyTwoWeekHigh")
        week52_low = info.get("fiftyTwoWeekLow")

        high_pct = None
        low_pct = None
        if current_price and week52_high and week52_high > 0:
            high_pct = round(((week52_high - current_price) / week52_high) * 100, 2)
        if current_price and week52_low and week52_low > 0:
            low_pct = round(((current_price - week52_low) / week52_low) * 100, 2)

        market_cap = info.get("marketCap")
        market_cap_cr = round(market_cap / 10_000_000, 0) if market_cap else None

        result.update({
            "market_cap_cr": market_cap_cr,
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "debt_to_equity": info.get("debtToEquity"),
            "roe_pct": (
                round(info.get("returnOnEquity", 0) * 100, 1)
                if info.get("returnOnEquity") else None
            ),
            "revenue_growth_pct": (
                round(info.get("revenueGrowth", 0) * 100, 1)
                if info.get("revenueGrowth") else None
            ),
            "week52_high": week52_high,
            "week52_low": week52_low,
            "week52_high_pct": high_pct,
            "week52_low_pct": low_pct,
            "near_52w_high": high_pct is not None and high_pct <= 3.0,
            "near_52w_low": low_pct is not None and low_pct <= 5.0,
            "avg_volume_10d": info.get("averageVolume10days"),
            "beta": info.get("beta"),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "confidence": 0.9,
        })
    except Exception as e:
        result["error"] = str(e)
        result["confidence"] = 0.0

    return result


def fetch_fii_dii_activity(ticker: str, sector: str) -> Dict[str, Any]:
    """
    Estimate FII/DII activity from institutional ownership.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "fii_activity": "neutral",
        "fii_signal": 0,
        "dii_activity": "neutral",
        "institution_pct": None,
        "confidence": 0.3,
        "fetched_at": datetime.datetime.now().isoformat(),
        "note": "FII data estimated from institutional ownership changes",
    }

    try:
        yf_ticker = get_nse_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        inst_pct = info.get("heldPercentInstitutions")
        if inst_pct:
            inst_pct_rounded = round(inst_pct * 100, 1)
            result["institution_pct"] = inst_pct_rounded
            if inst_pct_rounded > 45:
                result["fii_activity"] = "net_buyer"
                result["fii_signal"] = 1
            elif inst_pct_rounded < 20:
                result["fii_activity"] = "net_seller"
                result["fii_signal"] = -1
            result["confidence"] = 0.5
    except Exception as e:
        result["error"] = str(e)

    return result


def calc_earnings_surprise(actual: float, estimate: float) -> float:
    """
    Calculate earnings surprise percentage.
    ((actual - estimate) / abs(estimate)) * 100
    """
    if estimate == 0:
        return 0.0
    return round(((actual - estimate) / abs(estimate)) * 100, 2)


def get_surprise_label(surprise_pct: float) -> str:
    if surprise_pct >= 10:
        return "strong_beat"
    if surprise_pct >= 3:
        return "beat"
    if surprise_pct >= -3:
        return "inline"
    if surprise_pct >= -10:
        return "miss"
    return "strong_miss"


def fetch_peer_comparison(
    ticker: str,
    sector: str,
    current_pe: Optional[float],
    current_price: Optional[float],
) -> Dict[str, Any]:
    """
    Compare company against sector peers.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "peers": [],
        "sector_avg_pe": None,
        "relative_pe": None,
        "relative_strength": 0.5,
        "confidence": 0.0,
        "fetched_at": datetime.datetime.now().isoformat(),
    }

    peers = SECTOR_PEERS.get(ticker, [])
    if not peers:
        return result

    peer_pes = []
    for peer in peers[:3]:
        try:
            info = yf.Ticker(get_nse_ticker(peer)).info
            pe = info.get("trailingPE")
            if pe and 0 < pe < 200:
                peer_pes.append(pe)
            time.sleep(0.3)
        except Exception:
            continue

    if peer_pes:
        sector_avg_pe = round(sum(peer_pes) / len(peer_pes), 1)
        result["sector_avg_pe"] = sector_avg_pe
        result["peers"] = [{"ticker": p} for p in peers[:3]]
        if current_pe and current_pe > 0:
            result["relative_pe"] = round(current_pe / sector_avg_pe, 2)
            if result["relative_pe"] < 0.85:
                result["relative_strength"] = 0.75
            elif result["relative_pe"] > 1.20:
                result["relative_strength"] = 0.35
            else:
                result["relative_strength"] = 0.55
        result["confidence"] = 0.7

    return result


def run_layer1_financials(
    ticker: str,
    tenant_id: str = "0001",
    include_peers: bool = False,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Orchestrate financial data fetching for a company.
    """
    if verbose:
        print(f"  [{ticker}] Fetching OHLCV data...")
    ohlcv = fetch_intraday_ohlcv(ticker)

    if verbose:
        print(f"  [{ticker}] Fetching fundamentals...")
    fundamentals = fetch_fundamentals(ticker)

    if verbose:
        print(f"  [{ticker}] Fetching FII/DII activity...")
    fii_data = fetch_fii_dii_activity(ticker, "")

    peer_data: Dict[str, Any] = {}
    if include_peers:
        if verbose:
            print(f"  [{ticker}] Fetching peer comparison...")
        peer_data = fetch_peer_comparison(
            ticker, "",
            fundamentals.get("pe_ratio"),
            ohlcv.get("current_price"),
        )

    financial_data: Dict[str, Any] = {
        "ticker": ticker,
        "tenant_id": tenant_id,
        "ohlcv": ohlcv,
        "fundamentals": fundamentals,
        "fii_dii": fii_data,
        "peer_comparison": peer_data,
        "near_52w_high": fundamentals.get("near_52w_high", False),
        "near_52w_low": fundamentals.get("near_52w_low", False),
        "fii_activity": fii_data.get("fii_activity", "neutral"),
        "market_cap_cr": fundamentals.get("market_cap_cr"),
        "pe_ratio": fundamentals.get("pe_ratio"),
        "current_price": ohlcv.get("current_price"),
        "fetched_at": datetime.datetime.now().isoformat(),
    }
    return financial_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TradeIQ Layer 1 — Financial Data"
    )
    parser.add_argument("--ticker", type=str, default="RELIANCE")
    parser.add_argument("--peers", action="store_true")
    args = parser.parse_args()

    t = args.ticker.upper()
    print(f"\nTradeIQ Layer 1 Financials — {t}")
    print("=" * 60)
    data = run_layer1_financials(t, include_peers=args.peers)

    print("\nFinancial Summary:")
    print(f"  Current price:  ₹{data.get('current_price', 'N/A')}")
    print(f"  Market cap:     ₹{data.get('market_cap_cr', 'N/A')} Cr")
    print(f"  P/E ratio:      {data.get('pe_ratio', 'N/A')}")
    print(f"  FII activity:   {data.get('fii_activity', 'N/A')}")
    print(f"  Near 52W high:  {data.get('near_52w_high', False)}")
    print(f"  Near 52W low:   {data.get('near_52w_low', False)}")

