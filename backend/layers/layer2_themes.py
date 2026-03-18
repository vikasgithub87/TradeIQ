"""
layer2_themes.py — Sector theme scoring and rotation detection.
"""
import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

THEME_MIN_COMPANIES = 2
ROTATION_MIN_COMPANIES = 3


def calculate_theme_scores(
    company_scores: List[Dict[str, Any]],
    sector_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    sector_groups: Dict[str, List[Dict[str, Any]]] = {}
    for score in company_scores:
        ticker = score.get("ticker", "")
        sector = sector_map.get(ticker, "Unknown")
        sector_groups.setdefault(sector, []).append(score)

    themes: List[Dict[str, Any]] = []
    for sector, companies in sector_groups.items():
        if not companies:
            continue
        scores = [c.get("buy_score", 0) for c in companies]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        above_50 = [c for c in companies if c.get("buy_score", 0) >= 50]
        above_65 = [c for c in companies if c.get("buy_score", 0) >= 65]

        if len(scores) >= 2:
            top2 = sorted(scores, reverse=True)[:2]
            top2_avg = sum(top2) / 2
            theme_score = (avg_score * 0.4) + (top2_avg * 0.6)
        else:
            theme_score = avg_score

        if theme_score >= 70 and len(above_65) >= 2:
            theme_signal = "strong_buy"
        elif theme_score >= 55 and len(above_50) >= 2:
            theme_signal = "buy"
        elif theme_score >= 45:
            theme_signal = "watch"
        else:
            theme_signal = "neutral"

        top_companies = sorted(
            companies, key=lambda x: x.get("buy_score", 0), reverse=True
        )[:5]

        themes.append({
            "sector": sector,
            "theme_score": round(theme_score, 1),
            "signal": theme_signal,
            "company_count": len(companies),
            "above_threshold": len(above_65),
            "avg_score": round(avg_score, 1),
            "max_score": round(max_score, 1),
            "top_companies": [
                {
                    "ticker": c["ticker"],
                    "buy_score": c["buy_score"],
                    "signal": c["signal"],
                }
                for c in top_companies
            ],
        })

    return sorted(themes, key=lambda x: x["theme_score"], reverse=True)


def detect_sector_rotation(theme_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for theme in theme_scores:
        if (theme.get("above_threshold", 0) >= ROTATION_MIN_COMPANIES
                and theme.get("theme_score", 0) >= 60):
            alerts.append({
                "sector": theme["sector"],
                "alert_type": "sector_rotation",
                "strength": "strong" if theme["theme_score"] >= 75 else "moderate",
                "companies": theme["above_threshold"],
                "theme_score": theme["theme_score"],
                "message": (
                    f"{theme['above_threshold']} companies in {theme['sector']} "
                    f"scoring above threshold — possible sector rotation signal"
                ),
            })
    return alerts

