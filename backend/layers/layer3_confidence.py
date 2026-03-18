"""
layer3_confidence.py — Confidence score calculator for Layer 3.
Combines technical indicators, patterns, and levels into a single
confidence score (0-100) that validates the Layer 2 signal direction.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def calculate_confluence(
    indicators: dict,
    patterns: dict,
    levels: dict,
    direction: str,  # "BUY" or "SHORT"
    regime: str,
) -> dict:
    """
    Count how many independent technical signals agree with direction.
    More confluence = higher confidence.
    Returns confluence count and detailed breakdown.
    """
    signals_checked = []
    agreeing = 0

    is_buy = direction == "BUY"
    ema = indicators.get("ema", {}) or {}
    macd = indicators.get("macd", {}) or {}
    rsi = indicators.get("rsi")
    vol = indicators.get("volume", {}) or {}
    vwap_pos = levels.get("vwap_position", {}) or {}

    if ema.get("bull_aligned") is not None:
        agrees = bool(ema.get("bull_aligned")) if is_buy else bool(ema.get("bear_aligned", False))
        signals_checked.append({"indicator": "EMA alignment", "agrees": agrees})
        agreeing += 1 if agrees else 0

    if macd.get("bullish") is not None:
        agrees = bool(macd.get("bullish")) if is_buy else not bool(macd.get("bullish"))
        signals_checked.append({"indicator": "MACD", "agrees": agrees})
        agreeing += 1 if agrees else 0

    if rsi is not None:
        if is_buy:
            agrees = 30 < rsi < 70
        else:
            agrees = 30 < rsi < 75
        signals_checked.append({"indicator": f"RSI {rsi}", "agrees": agrees})
        agreeing += 1 if agrees else 0

    vwap_bull = vwap_pos.get("bullish_bias")
    if vwap_bull is not None:
        agrees = bool(vwap_bull) if is_buy else not bool(vwap_bull)
        signals_checked.append({"indicator": "VWAP position", "agrees": agrees})
        agreeing += 1 if agrees else 0

    if vol.get("confirms_move") is not None:
        agrees = bool(vol.get("confirms_move"))
        signals_checked.append({
            "indicator": f"Volume {vol.get('volume_ratio', 1):.1f}x",
            "agrees": agrees,
        })
        agreeing += 1 if agrees else 0

    dominant = patterns.get("dominant", "neutral")
    if dominant != "neutral":
        agrees = (dominant == "bullish") if is_buy else (dominant == "bearish")
        signals_checked.append({"indicator": f"Pattern: {dominant}", "agrees": agrees})
        agreeing += 1 if agrees else 0

    if is_buy and levels.get("pdh_breakout"):
        signals_checked.append({"indicator": "PDH breakout", "agrees": True})
        agreeing += 1
    elif (not is_buy) and levels.get("pdl_breakdown"):
        signals_checked.append({"indicator": "PDL breakdown", "agrees": True})
        agreeing += 1
    else:
        signals_checked.append({"indicator": "PDH/PDL", "agrees": False})

    total = len(signals_checked)
    return {
        "total_signals": total,
        "agreeing_signals": agreeing,
        "confluence_score": round(agreeing / total, 2) if total > 0 else 0,
        "breakdown": signals_checked,
    }


def calculate_confidence(
    l2_score: float,
    direction: str,
    indicators: dict,
    patterns: dict,
    levels: dict,
    regime: str,
    threshold: int = 60,
) -> dict:
    """
    Calculate the overall confidence score (0-100) for a signal.
    """
    breakdown = {}
    penalties = 0.0
    penalty_reasons = []
    time_quality = 1.0
    time_note = None
    hour_ist = None

    margin = max(0, l2_score - threshold)
    l2_pts = min(margin * 0.6, 30.0)
    breakdown["l2_margin"] = round(l2_pts, 1)

    confluence = calculate_confluence(indicators, patterns, levels, direction, regime)
    conf_pts = confluence["confluence_score"] * 40
    breakdown["confluence"] = round(conf_pts, 1)

    vol = indicators.get("volume", {}) or {}
    vol_ratio = vol.get("volume_ratio", 1.0)
    if vol_ratio >= 3.0:
        vol_pts = 15.0
    elif vol_ratio >= 2.0:
        vol_pts = 12.0
    elif vol_ratio >= 1.5:
        vol_pts = 8.0
    elif vol_ratio >= 1.0:
        vol_pts = 4.0
    else:
        vol_pts = 0.0
    breakdown["volume"] = round(vol_pts, 1)

    dominant = patterns.get("dominant", "neutral")
    bullish_c = patterns.get("bullish_count", 0)
    bearish_c = patterns.get("bearish_count", 0)

    if direction == "BUY" and dominant == "bullish":
        pat_pts = min(bullish_c * 3.5, 10.0)
    elif direction == "SHORT" and dominant == "bearish":
        pat_pts = min(bearish_c * 3.5, 10.0)
    else:
        pat_pts = 0.0
    breakdown["pattern"] = round(pat_pts, 1)

    rsi = indicators.get("rsi")
    if rsi is not None:
        if direction == "BUY" and rsi > 75:
            penalties += 12.0
            penalty_reasons.append(f"RSI overbought ({rsi:.0f})")
        elif direction == "SHORT" and rsi < 25:
            penalties += 12.0
            penalty_reasons.append(f"RSI oversold ({rsi:.0f}) bounce risk")

    if vol_ratio < 0.7:
        penalties += 15.0
        penalty_reasons.append(f"Very low volume ({vol_ratio:.1f}x avg)")
    elif vol_ratio < 1.0:
        penalties += 7.0
        penalty_reasons.append(f"Below average volume ({vol_ratio:.1f}x)")

    vwap_pos = levels.get("vwap_position", {}) or {}
    vwap_bull = vwap_pos.get("bullish_bias")
    if direction == "BUY" and vwap_bull is False:
        penalties += 8.0
        penalty_reasons.append("Price below VWAP — against institutional bias")
    elif direction == "SHORT" and vwap_bull is True:
        penalties += 8.0
        penalty_reasons.append("Price above VWAP — against short bias")

    if regime == "HIGH_VOLATILITY":
        penalties += 5.0
        penalty_reasons.append("High volatility regime — wider stops needed")
    elif regime == "EXPIRY_CAUTION":
        penalties += 3.0
        penalty_reasons.append("Expiry day — pin risk")

    bb = indicators.get("bollinger", {}) or {}
    if bb.get("squeeze"):
        breakdown["pattern"] = round(breakdown["pattern"] + 5.0, 1)

    # ── Time of day penalty ───────────────────────────────────────────
    # Signals generated after 13:30 IST have less time to hit targets
    # and carry overnight gap risk if not squared off
    try:
        import datetime as _dt

        now_ist = _dt.datetime.utcnow() + _dt.timedelta(hours=5, minutes=30)
        hour_ist = now_ist.hour + now_ist.minute / 60.0

        time_quality = 1.0  # default full quality
        time_note = None

        if 9.25 <= hour_ist < 10.5:
            time_quality = 1.0  # Golden hour — best entry window
        elif 10.5 <= hour_ist < 12.0:
            time_quality = 0.95  # Good window
        elif 12.0 <= hour_ist < 13.5:
            time_quality = 0.85  # Mid session — acceptable
        elif 13.5 <= hour_ist < 14.5:
            time_quality = 0.70  # Late session — time decay begins
            time_note = "Late session — less time to hit target"
        elif 14.5 <= hour_ist < 15.0:
            time_quality = 0.50  # Last hour — high risk
            time_note = "Final hour — gap risk, avoid new entries"
            penalties += 10.0
            penalty_reasons.append("Final trading hour — high gap risk")
        elif hour_ist >= 15.0 or hour_ist < 9.25:
            time_quality = 0.0  # Market closed
            time_note = "Market closed"

        breakdown["time_quality"] = round(time_quality * 5, 1)  # max 5 pts bonus

        if time_note and time_note not in penalty_reasons:
            if time_quality < 0.7:
                penalty_reasons.append(time_note)
    except Exception:
        pass

    raw_score = sum(breakdown.values())
    final_score = max(0.0, min(100.0, raw_score - penalties))

    if confluence["confluence_score"] >= 0.7:
        alignment = "strongly_confirms"
    elif confluence["confluence_score"] >= 0.5:
        alignment = "confirms"
    elif confluence["confluence_score"] >= 0.3:
        alignment = "neutral"
    else:
        alignment = "contradicts"

    return {
        "confidence_score": round(final_score, 1),
        "raw_score": round(raw_score, 1),
        "penalties": round(penalties, 1),
        "penalty_reasons": penalty_reasons,
        "breakdown": breakdown,
        "confluence": confluence,
        "technical_alignment": alignment,
        "pass_to_trade": final_score >= 60,
        "time_quality": time_quality,
        "time_note": time_note,
        "optimal_entry_window": bool(hour_ist is not None and 9.25 <= hour_ist < 12.0),
    }

