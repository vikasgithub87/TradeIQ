"""
layer2_scoring.py — TradeIQ Layer 2: BUY Scoring Model.
"""
import os
import sys
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def score_to_signal(score: float) -> str:
    if score >= 75:
        return "strong_buy"
    if score >= 60:
        return "buy"
    if score >= 45:
        return "moderate_buy"
    if score >= 25:
        return "watch"
    return "avoid"


def score_news_sentiment(intel: Dict[str, Any]) -> float:
    net = intel.get("net_sentiment_score", 0.0) or 0.0
    rel = intel.get("intraday_relevance", "LOW")
    n_long = len(intel.get("long_catalysts", []) or [])

    if net <= 0:
        return 0.0

    base = net * 18.0
    rel_mult = 1.0 if rel == "HIGH" else 0.7 if rel == "MEDIUM" else 0.4
    catalyst_bonus = min(n_long * 0.8, 4.0)
    raw = (base * rel_mult) + catalyst_bonus
    return round(min(raw, 22.0), 2)


def score_earnings_surprise(intel: Dict[str, Any]) -> float:
    earnings = intel.get("earnings", {}) or {}
    surprise = earnings.get("eps_surprise_pct")
    guidance = earnings.get("guidance", "unknown")
    if surprise is None or surprise <= 0:
        return 0.0

    if surprise >= 15:
        base = 16.0
    elif surprise >= 10:
        base = 14.0
    elif surprise >= 5:
        base = 10.0
    elif surprise >= 2:
        base = 6.0
    else:
        base = 2.0

    guidance_bonus = 0.0
    if guidance in ("likely_raised", "raised"):
        guidance_bonus = 2.0
    elif guidance in ("maintained_positive",):
        guidance_bonus = 1.0

    return round(min(base + guidance_bonus, 18.0), 2)


def score_product_launch(intel: Dict[str, Any]) -> float:
    long_cats = intel.get("long_catalysts", []) or []
    high_impact = {
        "product_launch", "contract_win", "capacity_expansion",
        "buyback_announced",
    }
    medium_impact = {"dividend_declared", "analyst_coverage"}

    score = 0.0
    for cat in long_cats:
        cat_type = cat.get("type", "")
        intensity = cat.get("intensity", 0.0) or 0.0
        relevance = cat.get("intraday_relevance", "LOW")
        if cat_type in high_impact:
            base = 10.0 * intensity
            if relevance == "HIGH":
                base *= 1.3
            score += base
        elif cat_type in medium_impact:
            score += 4.0 * intensity

    return round(min(score, 14.0), 2)


def score_fii_activity(intel: Dict[str, Any]) -> float:
    fii = intel.get("fii_activity", "neutral")
    fii_dii = intel.get("fii_dii", {}) or {}
    inst_pct = fii_dii.get("institution_pct") or 0

    if fii == "net_buyer":
        base = 12.0
        if inst_pct > 50:
            base += 2.0
        return round(min(base, 14.0), 2)
    if fii == "neutral":
        return round(inst_pct * 0.06, 2) if inst_pct else 4.0
    return 0.0


def score_sector_tailwind(intel: Dict[str, Any], theme_score: float = 0.0) -> float:
    base = theme_score * 0.12
    long_cats = intel.get("long_catalysts", []) or []
    for cat in long_cats:
        if cat.get("type") == "sector_tailwind":
            base += (cat.get("intensity") or 0.0) * 4.0
            break
    return round(min(base, 12.0), 2)


def score_google_trends(intel: Dict[str, Any]) -> float:
    if intel.get("google_trends_spike"):
        return 10.0
    summary = (intel.get("catalyst_summary") or "").lower()
    if any(k in summary for k in ["trending", "viral", "search spike", "popular"]):
        return 5.0
    return 0.0


def score_promoter_activity(intel: Dict[str, Any]) -> float:
    pledge_pct = intel.get("promoter_pledge_pct") or 0.0
    long_cats = intel.get("long_catalysts", []) or []
    for cat in long_cats:
        if cat.get("type") == "promoter_buying":
            return round(min(6.0 * (cat.get("intensity") or 0.5), 6.0), 2)

    if pledge_pct > 30:
        return 0.0
    if pledge_pct > 15:
        return 1.0
    if pledge_pct > 5:
        return 2.5
    return 3.0


def score_oi_buildup(intel: Dict[str, Any]) -> float:
    pcr = intel.get("pcr") or 1.0
    oi_signal = intel.get("oi_signal", "neutral")
    if oi_signal == "strong_long_buildup" and pcr >= 1.3:
        return 4.0
    if oi_signal == "long_buildup" and pcr >= 1.1:
        return 3.0
    if oi_signal == "neutral" and pcr >= 0.9:
        return 1.5
    return 0.0


SHORT_WEIGHTS = {
    "negative_news": 25,
    "earnings_miss": 20,
    "fii_selling": 15,
    "short_oi_buildup": 15,
    "promoter_pledge": 12,
    "sector_headwind": 8,
    "exhaustion_signal": 5,
}


def short_to_signal(score: float) -> str:
    """Convert short score to signal label."""
    if score >= 80:
        return "strong_short"
    elif score >= 65:
        return "short"
    elif score >= 50:
        return "moderate_short"
    elif score >= 35:
        return "watch_short"
    else:
        return "no_short"


def calculate_short_score(intel: dict) -> dict:
    """
    Calculate SHORT score for a company. Max 100 points.
    Uses 7 bearish factors. Returns score + full breakdown.
    """
    ticker = intel.get("ticker", "UNKNOWN")

    market_cap = intel.get("market_cap_cr", 0) or 0
    if market_cap > 0 and market_cap < 2000:
        return {
            "ticker": ticker,
            "short_score": 0.0,
            "short_signal": "no_short",
            "filtered_reason": f"Market cap ₹{market_cap}Cr below minimum",
            "short_breakdown": {},
            "short_top_factors": [],
            "short_flags": ["LOW_LIQUIDITY"],
        }

    breakdown: Dict[str, float] = {}

    net = intel.get("net_sentiment_score", 0.0) or 0.0
    rel = intel.get("intraday_relevance", "LOW")
    n_short_cats = len(intel.get("short_catalysts", []) or [])
    if net < 0:
        base = abs(net) * 20.0
        rel_mult = 1.0 if rel == "HIGH" else 0.7 if rel == "MEDIUM" else 0.4
        cat_bonus = min(n_short_cats * 0.8, 5.0)
        breakdown["negative_news"] = round(
            min((base * rel_mult) + cat_bonus, 25.0), 2
        )
    else:
        breakdown["negative_news"] = 0.0

    earnings = intel.get("earnings", {}) or {}
    surprise = earnings.get("eps_surprise_pct")
    guidance = earnings.get("guidance", "unknown")
    if surprise is not None and surprise < 0:
        miss_abs = abs(surprise)
        if miss_abs >= 15:
            base = 18.0
        elif miss_abs >= 10:
            base = 14.0
        elif miss_abs >= 5:
            base = 10.0
        elif miss_abs >= 2:
            base = 6.0
        else:
            base = 2.0
        guidance_bonus = (
            2.0
            if guidance in ("likely_cut", "cut")
            else 1.0
            if guidance == "maintained_cautious"
            else 0.0
        )
        breakdown["earnings_miss"] = round(min(base + guidance_bonus, 20.0), 2)
    else:
        breakdown["earnings_miss"] = 0.0

    fii = intel.get("fii_activity", "neutral")
    breakdown["fii_selling"] = (
        15.0 if fii == "net_seller" else (4.0 if fii == "neutral" else 0.0)
    )

    pcr = intel.get("pcr", 1.0) or 1.0
    oi_signal = intel.get("oi_signal", "neutral")
    if oi_signal == "strong_short_buildup" and pcr < 0.5:
        breakdown["short_oi_buildup"] = 15.0
    elif oi_signal == "short_buildup" and pcr < 0.6:
        breakdown["short_oi_buildup"] = 10.0
    elif pcr < 0.7:
        breakdown["short_oi_buildup"] = 5.0
    else:
        breakdown["short_oi_buildup"] = 0.0

    pledge = intel.get("promoter_pledge_pct", 0.0) or 0.0
    if pledge >= 30:
        breakdown["promoter_pledge"] = 12.0
    elif pledge >= 20:
        breakdown["promoter_pledge"] = 8.0
    elif pledge >= 10:
        breakdown["promoter_pledge"] = 4.0
    else:
        breakdown["promoter_pledge"] = 0.0

    short_cats = intel.get("short_catalysts", []) or []
    headwind = 0.0
    for cat in short_cats:
        if cat.get("type") == "sector_headwind":
            headwind = (cat.get("intensity") or 0) * 8.0
            break
    breakdown["sector_headwind"] = round(min(headwind, 8.0), 2)

    near_high = intel.get("near_52w_high", False)
    has_neg_news = any(
        c.get("intraday_relevance") == "HIGH" for c in short_cats
    )
    breakdown["exhaustion_signal"] = (
        5.0 if near_high and has_neg_news else (2.0 if near_high else 0.0)
    )

    raw_score = sum(breakdown.values())

    short_flags: List[str] = []
    penalties = 0.0

    n_long = len(intel.get("long_catalysts", []) or [])
    if n_long > 0:
        penalties += min(n_long * 2.0, 6.0)
        short_flags.append("CONFLICTING_LONG_SIGNALS")

    if intel.get("near_52w_low"):
        penalties += 6.0
        short_flags.append("NEAR_52W_LOW_BOUNCE_RISK")

    final_score = max(0.0, min(100.0, raw_score - penalties))

    top_factors = sorted(
        [(k, v) for k, v in breakdown.items() if v > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    return {
        "ticker": ticker,
        "short_score": round(final_score, 1),
        "short_signal": short_to_signal(final_score),
        "short_breakdown": {k: round(v, 2) for k, v in breakdown.items()},
        "raw_short_score": round(raw_score, 1),
        "short_penalties": round(penalties, 1),
        "short_top_factors": [f[0] for f in top_factors],
        "short_flags": short_flags,
    }


def calculate_buy_score(intel: Dict[str, Any], theme_score: float = 0.0) -> Dict[str, Any]:
    ticker = intel.get("ticker", "UNKNOWN")
    market_cap = intel.get("market_cap_cr") or 0
    if 0 < market_cap < 2000:
        return {
            "ticker": ticker,
            "buy_score": 0.0,
            "signal": "avoid",
            "filtered_reason": f"Market cap ₹{market_cap}Cr below ₹2000Cr minimum",
            "score_breakdown": {
                "news_sentiment": 0.0,
                "earnings_surprise": 0.0,
                "product_launch": 0.0,
                "fii_activity": 0.0,
                "sector_tailwind": 0.0,
                "google_trends": 0.0,
                "promoter_activity": 0.0,
                "oi_buildup": 0.0,
            },
            "top_factors": [],
            "flags": ["LOW_LIQUIDITY"],
            "catalyst_summary": intel.get("catalyst_summary", ""),
            "dominant_direction": intel.get("dominant_direction", "NEUTRAL"),
            "intraday_relevance": intel.get("intraday_relevance", "LOW"),
        }

    breakdown = {
        "news_sentiment":    score_news_sentiment(intel),
        "earnings_surprise": score_earnings_surprise(intel),
        "product_launch":    score_product_launch(intel),
        "fii_activity":      score_fii_activity(intel),
        "sector_tailwind":   score_sector_tailwind(intel, theme_score),
        "google_trends":     score_google_trends(intel),
        "promoter_activity": score_promoter_activity(intel),
        "oi_buildup":        score_oi_buildup(intel),
    }

    raw_score = sum(breakdown.values())
    penalties = 0.0
    flags: List[str] = []

    if intel.get("near_52w_high"):
        penalties += 5.0
        flags.append("NEAR_52W_HIGH")

    if intel.get("in_results_window") and intel.get("results_expected"):
        penalties += 3.0
        flags.append("RESULTS_WINDOW")

    pledge = intel.get("promoter_pledge_pct") or 0.0
    if pledge > 25:
        penalties += 4.0
        flags.append("HIGH_PLEDGE")

    if intel.get("short_catalysts"):
        n_short = len(intel.get("short_catalysts") or [])
        penalties += min(n_short * 2.0, 6.0)
        flags.append("CONFLICTING_SIGNALS")

    final_score = max(0.0, min(100.0, raw_score - penalties))

    top_factors = sorted(
        [(k, v) for k, v in breakdown.items()],
        key=lambda x: x[1],
        reverse=True,
    )[:3]
    top_names = [f[0] for f in top_factors if f[1] > 0]

    return {
        "ticker": ticker,
        "buy_score": round(final_score, 1),
        "signal": score_to_signal(final_score),
        "score_breakdown": {k: round(v, 2) for k, v in breakdown.items()},
        "raw_score": round(raw_score, 1),
        "penalties": round(penalties, 1),
        "top_factors": top_names,
        "flags": flags,
        "catalyst_summary": intel.get("catalyst_summary", ""),
        "dominant_direction": intel.get("dominant_direction", "NEUTRAL"),
        "intraday_relevance": intel.get("intraday_relevance", "LOW"),
    }


def filter_by_regime(scores: List[Dict[str, Any]], threshold: int) -> List[Dict[str, Any]]:
    filtered = [
        s for s in scores
        if s.get("buy_score", 0) >= threshold
        and "LOW_LIQUIDITY" not in (s.get("flags") or [])
    ]
    return sorted(filtered, key=lambda x: x["buy_score"], reverse=True)

