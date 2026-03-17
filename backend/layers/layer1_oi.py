"""
layer1_oi.py — F&O Open Interest and Put-Call Ratio calculation.
"""
import os
import sys
import datetime
from typing import Dict, Any

try:
    import yfinance as yf
except ImportError:
    raise ImportError("Run: pip install yfinance")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.layers.layer1_financials import get_nse_ticker


def calc_pcr(put_oi: float, call_oi: float) -> float:
    """
    Calculate Put-Call Ratio.
    """
    if call_oi <= 0:
        return 1.0
    return round(put_oi / call_oi, 4)


def get_oi_signal(pcr: float) -> str:
    if pcr >= 1.3:
        return "strong_long_buildup"
    if pcr >= 1.1:
        return "long_buildup"
    if pcr >= 0.9:
        return "neutral"
    if pcr >= 0.7:
        return "short_buildup"
    return "strong_short_buildup"


def fetch_oi_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch F&O Open Interest data from yfinance options chain.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "pcr": 1.0,
        "oi_signal": "neutral",
        "total_put_oi": 0,
        "total_call_oi": 0,
        "max_pain": None,
        "atm_strike": None,
        "expiry_date": None,
        "confidence": 0.0,
        "fetched_at": datetime.datetime.now().isoformat(),
        "error": None,
    }

    try:
        yf_ticker = get_nse_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        expirations = stock.options
        if not expirations:
            result["error"] = f"No options data for {ticker}"
            return result

        expiry = expirations[0]
        result["expiry_date"] = expiry
        chain = stock.option_chain(expiry)
        calls = chain.calls
        puts = chain.puts
        if calls.empty or puts.empty:
            result["error"] = "Empty options chain"
            return result

        total_call_oi = int(calls["openInterest"].sum())
        total_put_oi = int(puts["openInterest"].sum())
        pcr = calc_pcr(total_put_oi, total_call_oi)

        try:
            current_price = stock.info.get("regularMarketPrice", 0)
            atm_strike = None
            max_pain = None
            if current_price:
                all_strikes = sorted(calls["strike"].tolist())
                atm_strike = min(all_strikes, key=lambda s: abs(s - current_price))
                call_oi_by_strike = dict(zip(calls["strike"], calls["openInterest"]))
                put_oi_by_strike = dict(zip(puts["strike"], puts["openInterest"]))
                all_strikes_set = set(call_oi_by_strike) | set(put_oi_by_strike)
                max_combined = max(
                    (
                        call_oi_by_strike.get(s, 0) + put_oi_by_strike.get(s, 0),
                        s,
                    )
                    for s in all_strikes_set
                )
                max_pain = max_combined[1]
        except Exception:
            atm_strike = None
            max_pain = None

        result.update({
            "pcr": pcr,
            "oi_signal": get_oi_signal(pcr),
            "total_put_oi": total_put_oi,
            "total_call_oi": total_call_oi,
            "max_pain": max_pain,
            "atm_strike": atm_strike,
            "confidence": 0.85,
        })
    except Exception as e:
        result["error"] = str(e)
        result["confidence"] = 0.0

    return result

