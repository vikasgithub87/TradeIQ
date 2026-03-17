"""
layer1_earnings.py — Earnings calendar detection and surprise calculation.
"""
import os
import sys
import datetime
from typing import Optional, Dict, Any

try:
    import yfinance as yf
except ImportError:
    raise ImportError("Run: pip install yfinance")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.layers.layer1_financials import (
    get_nse_ticker,
    calc_earnings_surprise,
    get_surprise_label,
)


def is_results_window(date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Detect if we are currently in quarterly results season.
    """
    if not date:
        date = datetime.date.today()

    month = date.month
    day = date.day

    windows = [
        {"quarter": "Q1", "period": "Apr-Jun", "start": (7, 15), "end": (8, 20)},
        {"quarter": "Q2", "period": "Jul-Sep", "start": (10, 15), "end": (11, 20)},
        {"quarter": "Q3", "period": "Oct-Dec", "start": (1, 15), "end": (2, 20)},
        {"quarter": "Q4", "period": "Jan-Mar", "start": (4, 15), "end": (5, 31)},
    ]

    in_window = False
    current_quarter = None
    for w in windows:
        sm, sd = w["start"]
        em, ed = w["end"]
        if sm > em:
            in_range = (month == sm and day >= sd) or (month == em and day <= ed)
        else:
            in_range = (
                (month == sm and day >= sd)
                or (month > sm and month < em)
                or (month == em and day <= ed)
            )
        if in_range:
            in_window = True
            current_quarter = w
            break

    return {
        "in_results_window": in_window,
        "current_quarter": current_quarter.get("quarter") if current_quarter else None,
        "quarter_period": current_quarter.get("period") if current_quarter else None,
        "results_expected": in_window,
        "checked_date": date.strftime("%Y-%m-%d"),
    }


def fetch_earnings_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch earnings history and calculate EPS surprise.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "announced": False,
        "latest_quarter": None,
        "eps_actual": None,
        "eps_estimate": None,
        "eps_surprise_pct": None,
        "surprise_label": None,
        "revenue_actual": None,
        "revenue_estimate": None,
        "revenue_surprise_pct": None,
        "guidance": "unknown",
        "in_results_window": False,
        "results_expected": False,
        "confidence": 0.0,
        "fetched_at": datetime.datetime.now().isoformat(),
        "error": None,
    }

    window = is_results_window()
    result["in_results_window"] = window["in_results_window"]
    result["results_expected"] = window["results_expected"]
    result["current_quarter"] = window.get("current_quarter")

    try:
        yf_ticker = get_nse_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        earnings = stock.earnings_history
        if earnings is not None and not earnings.empty:
            latest = earnings.iloc[-1]
            eps_actual = latest.get("epsActual")
            eps_estimate = latest.get("epsEstimate")
            if eps_actual is not None and eps_estimate is not None:
                surprise = calc_earnings_surprise(float(eps_actual), float(eps_estimate))
                result.update({
                    "announced": True,
                    "eps_actual": round(float(eps_actual), 2),
                    "eps_estimate": round(float(eps_estimate), 2),
                    "eps_surprise_pct": surprise,
                    "surprise_label": get_surprise_label(surprise),
                    "latest_quarter": str(getattr(latest, "name", ""))[:10],
                    "confidence": 0.85,
                })
                if surprise > 8:
                    result["guidance"] = "likely_raised"
                elif surprise > 3:
                    result["guidance"] = "maintained_positive"
                elif surprise < -8:
                    result["guidance"] = "likely_cut"
                elif surprise < -3:
                    result["guidance"] = "maintained_cautious"
                else:
                    result["guidance"] = "maintained"
    except Exception as e:
        result["error"] = str(e)
        result["confidence"] = 0.0

    return result


def fetch_promoter_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch promoter holding percentage and rough pledge trend.
    """
    result: Dict[str, Any] = {
        "ticker": ticker,
        "promoter_holding_pct": None,
        "promoter_pledge_pct": 0.0,
        "pledge_trend": "stable",
        "insider_pct": None,
        "confidence": 0.3,
        "fetched_at": datetime.datetime.now().isoformat(),
        "note": "Pledge data estimated — use BSE filings for precise values",
    }

    try:
        yf_ticker = get_nse_ticker(ticker)
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        insider_pct = info.get("heldPercentInsiders")
        if insider_pct:
            pct = round(insider_pct * 100, 1)
            result["promoter_holding_pct"] = pct
            result["insider_pct"] = pct
            result["confidence"] = 0.6
            if pct < 30:
                pledge = round(max(0, 40 - pct) * 0.3, 1)
                result["promoter_pledge_pct"] = pledge
                if pledge > 15:
                    result["pledge_trend"] = "high_risk"
                elif pledge > 8:
                    result["pledge_trend"] = "watch"
    except Exception as e:
        result["error"] = str(e)

    return result

