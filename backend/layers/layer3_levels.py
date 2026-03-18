"""
layer3_levels.py — Support/resistance, VWAP, PDH/PDL for NSE intraday.
These are the key price levels every professional intraday trader uses.
"""
import os
import sys
import pandas as pd
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def calc_vwap(candles: list) -> Optional[float]:
    """
    Volume Weighted Average Price for today's session.
    The most important intraday reference level on NSE.
    """
    try:
        df = pd.DataFrame(candles)
        for col in ["high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna()
        if df.empty:
            return None
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        total_vol = df["volume"].sum()
        if total_vol == 0:
            return None
        vwap = (typical_price * df["volume"]).sum() / total_vol
        return round(float(vwap), 2)
    except Exception:
        return None


def get_pdh_pdl(ticker: str) -> dict:
    """
    Previous Day High and Low — most reliable S/R for intraday NSE.
    Fetches yesterday's data from yfinance.
    """
    result = {"pdh": None, "pdl": None, "pdc": None}
    try:
        import yfinance as yf

        yf_ticker = ticker + ".NS"
        hist = yf.Ticker(yf_ticker).history(period="5d", interval="1d")
        if hist.empty or len(hist) < 2:
            return result
        prev = hist.iloc[-2]
        result["pdh"] = round(float(prev["High"]), 2)
        result["pdl"] = round(float(prev["Low"]), 2)
        result["pdc"] = round(float(prev["Close"]), 2)
    except Exception:
        pass
    return result


def calc_pivot_points(pdh: float, pdl: float, pdc: float) -> dict:
    """
    Classic pivot points — widely used on NSE for intraday S/R.
    PP = (H + L + C) / 3
    """
    if not all([pdh, pdl, pdc]):
        return {}
    pp = (pdh + pdl + pdc) / 3
    r1 = (2 * pp) - pdl
    r2 = pp + (pdh - pdl)
    r3 = pdh + 2 * (pp - pdl)
    s1 = (2 * pp) - pdh
    s2 = pp - (pdh - pdl)
    s3 = pdl - 2 * (pdh - pp)
    return {
        "pp": round(pp, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "r3": round(r3, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
        "s3": round(s3, 2),
    }


def find_support_resistance(candles: list, n_levels: int = 3) -> dict:
    """
    Find support and resistance levels from recent price action.
    Uses local highs and lows from the last 50 candles.
    """
    result = {"support": [], "resistance": []}
    try:
        if not candles or len(candles) < 10:
            return result
        df = pd.DataFrame(candles)
        closes = pd.to_numeric(df["close"], errors="coerce").dropna().tail(50)
        highs = pd.to_numeric(df["high"], errors="coerce").dropna().tail(50)
        lows = pd.to_numeric(df["low"], errors="coerce").dropna().tail(50)

        current = float(closes.iloc[-1])

        resistance_candidates = []
        for i in range(1, len(highs) - 1):
            if highs.iloc[i] > highs.iloc[i - 1] and highs.iloc[i] > highs.iloc[i + 1]:
                resistance_candidates.append(float(highs.iloc[i]))

        support_candidates = []
        for i in range(1, len(lows) - 1):
            if lows.iloc[i] < lows.iloc[i - 1] and lows.iloc[i] < lows.iloc[i + 1]:
                support_candidates.append(float(lows.iloc[i]))

        result["resistance"] = sorted(
            [round(r, 2) for r in resistance_candidates if r > current]
        )[:n_levels]
        result["support"] = sorted(
            [round(s, 2) for s in support_candidates if s < current],
            reverse=True,
        )[:n_levels]

    except Exception:
        pass
    return result


def analyse_vwap_position(current_price: float, vwap: Optional[float]) -> dict:
    """
    Classify price position relative to VWAP.
    Above VWAP = institutional buying bias.
    Below VWAP = institutional selling bias.
    """
    if not vwap or not current_price:
        return {"position": "unknown", "deviation_pct": None}

    deviation_pct = ((current_price - vwap) / vwap) * 100
    if deviation_pct > 0.5:
        position = "strongly_above"
    elif deviation_pct > 0:
        position = "above"
    elif deviation_pct > -0.5:
        position = "below"
    else:
        position = "strongly_below"

    return {
        "position": position,
        "deviation_pct": round(deviation_pct, 2),
        "bullish_bias": deviation_pct > 0,
    }


def get_all_levels(ticker: str, candles: list) -> dict:
    """
    Orchestrate all level calculations for a company.
    Returns complete levels dict.
    """
    current_price = None
    if candles:
        try:
            current_price = float(
                pd.to_numeric(pd.Series([c["close"] for c in candles]), errors="coerce")
                .dropna()
                .iloc[-1]
            )
        except Exception:
            pass

    vwap = calc_vwap(candles)
    pdhl = get_pdh_pdl(ticker)
    pivots = calc_pivot_points(pdhl.get("pdh"), pdhl.get("pdl"), pdhl.get("pdc"))
    sr = find_support_resistance(candles)
    vwap_pos = analyse_vwap_position(current_price, vwap)

    pdh_breakout = bool(current_price and pdhl.get("pdh") and current_price > pdhl["pdh"])
    pdl_breakdown = bool(current_price and pdhl.get("pdl") and current_price < pdhl["pdl"])

    return {
        "current_price": current_price,
        "vwap": vwap,
        "vwap_position": vwap_pos,
        "pdh": pdhl.get("pdh"),
        "pdl": pdhl.get("pdl"),
        "pdc": pdhl.get("pdc"),
        "pdh_breakout": pdh_breakout,
        "pdl_breakdown": pdl_breakdown,
        "pivot_points": pivots,
        "support_levels": sr.get("support", []),
        "resistance_levels": sr.get("resistance", []),
        "nearest_resistance": sr["resistance"][0] if sr.get("resistance") else None,
        "nearest_support": sr["support"][0] if sr.get("support") else None,
    }

