"""
layer3_patterns.py — Candlestick pattern detection for NSE intraday.
Detects 8 high-reliability patterns used by Indian intraday traders.
"""
import os
import sys
import pandas as pd
from typing import Optional  # noqa: F401

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def detect_patterns(candles: list) -> dict:
    """
    Detect candlestick patterns from OHLCV candle list.
    Returns dict with detected patterns and dominant signal.
    """
    result = {
        "patterns": [],
        "dominant": "none",
        "bullish_count": 0,
        "bearish_count": 0,
        "gap_up": False,
        "gap_down": False,
        "gap_pct": None,
    }

    if not candles or len(candles) < 3:
        return result

    try:
        df = pd.DataFrame(candles)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna().reset_index(drop=True)
        if len(df) < 3:
            return result
    except Exception:
        return result

    patterns = []

    if len(df) >= 2:
        prev_close = float(df["close"].iloc[-2])
        curr_open = float(df["open"].iloc[-1])
        if prev_close > 0:
            gap_pct = ((curr_open - prev_close) / prev_close) * 100
            result["gap_pct"] = round(gap_pct, 2)
            if gap_pct > 0.5:
                result["gap_up"] = True
                patterns.append({
                    "name": "gap_up",
                    "direction": "bullish",
                    "strength": min(gap_pct / 2, 1.0),
                })
            elif gap_pct < -0.5:
                result["gap_down"] = True
                patterns.append({
                    "name": "gap_down",
                    "direction": "bearish",
                    "strength": min(abs(gap_pct) / 2, 1.0),
                })

    c0 = df.iloc[-3]
    c1 = df.iloc[-2]
    c2 = df.iloc[-1]

    o0, h0, l0, cl0 = float(c0.open), float(c0.high), float(c0.low), float(c0.close)
    o1, h1, l1, cl1 = float(c1.open), float(c1.high), float(c1.low), float(c1.close)
    o2, h2, l2, cl2 = float(c2.open), float(c2.high), float(c2.low), float(c2.close)

    body1 = abs(cl1 - o1)
    body2 = abs(cl2 - o2)
    range1 = h1 - l1 if h1 > l1 else 0.001
    range2 = h2 - l2 if h2 > l2 else 0.001

    if (
        cl1 < o1
        and cl2 > o2
        and o2 <= cl1
        and cl2 >= o1
        and body2 > body1 * 0.8
    ):
        patterns.append({"name": "bullish_engulfing", "direction": "bullish", "strength": 0.85})

    if (
        cl1 > o1
        and cl2 < o2
        and o2 >= cl1
        and cl2 <= o1
        and body2 > body1 * 0.8
    ):
        patterns.append({"name": "bearish_engulfing", "direction": "bearish", "strength": 0.85})

    lower_shadow = (o2 - l2) if cl2 >= o2 else (cl2 - l2)
    upper_shadow = (h2 - cl2) if cl2 >= o2 else (h2 - o2)
    if lower_shadow >= body2 * 2 and upper_shadow <= body2 * 0.3 and body2 > 0:
        patterns.append({"name": "hammer", "direction": "bullish", "strength": 0.75})

    upper_shadow2 = h2 - max(o2, cl2)
    lower_shadow2 = min(o2, cl2) - l2
    if upper_shadow2 >= body2 * 2 and lower_shadow2 <= body2 * 0.3 and body2 > 0:
        patterns.append({"name": "shooting_star", "direction": "bearish", "strength": 0.75})

    if body2 <= range2 * 0.1 and range2 > 0:
        patterns.append({"name": "doji", "direction": "neutral", "strength": 0.5})

    if cl2 > o2 and body2 >= range2 * 0.85 and range2 > 0:
        patterns.append({"name": "bullish_marubozu", "direction": "bullish", "strength": 0.80})

    if cl2 < o2 and body2 >= range2 * 0.85 and range2 > 0:
        patterns.append({"name": "bearish_marubozu", "direction": "bearish", "strength": 0.80})

    if h2 <= h1 and l2 >= l1:
        patterns.append({"name": "inside_bar", "direction": "neutral", "strength": 0.60})

    if (
        cl0 < o0
        and body1 <= range1 * 0.3
        and cl2 > o2
        and cl2 > (o0 + cl0) / 2
    ):
        patterns.append({"name": "morning_star", "direction": "bullish", "strength": 0.90})

    if (
        cl0 > o0
        and body1 <= range1 * 0.3
        and cl2 < o2
        and cl2 < (o0 + cl0) / 2
    ):
        patterns.append({"name": "evening_star", "direction": "bearish", "strength": 0.90})

    bullish = [p for p in patterns if p["direction"] == "bullish"]
    bearish = [p for p in patterns if p["direction"] == "bearish"]

    result["patterns"] = patterns
    result["bullish_count"] = len(bullish)
    result["bearish_count"] = len(bearish)

    if bullish and (
        not bearish
        or sum(p["strength"] for p in bullish) > sum(p["strength"] for p in bearish)
    ):
        result["dominant"] = "bullish"
    elif bearish:
        result["dominant"] = "bearish"
    else:
        result["dominant"] = "neutral"

    return result

