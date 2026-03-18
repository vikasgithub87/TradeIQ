"""
smart_scan.py — Resolves category to company list and runs
the full Layer 1 + Layer 2 pipeline with live progress updates.
"""

import datetime
import json
import os
import sys
import time
from typing import Generator, Optional, List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.data.scan_categories import (  # noqa: E402
    NIFTY50_TICKERS,
    BUDGET_IMPACTED,
    WAR_IMPACTED,
    AI_IMPACTED,
    DOLLAR_APPRECIATION,
    EV_IMPACTED,
    RECENT_IPOS,
)

INTEL_DIR = "backend/data/company_intel"
SCORES_DIR = "backend/data/scores"
PROFILE_FILE = "backend/data/scan_profile.json"


def load_profile() -> dict:
    """Load saved scan profile from disk."""
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "last_category": "nifty50",
        "last_count": 20,
        "default_category": "nifty50",
        "default_count": 20,
        "last_run_at": None,
        "scheduled_time": "08:00",
        "email_enabled": False,
        "email_address": "",
        "run_history": [],
    }


def save_profile(profile: dict) -> None:
    """Save scan profile to disk."""
    try:
        os.makedirs("backend/data", exist_ok=True)
        with open(PROFILE_FILE, "w") as f:
            json.dump(profile, f, indent=2)
    except Exception:
        pass


def resolve_category(
    category: str,
    count: int = 20,
    date_str: Optional[str] = None,
) -> list:
    """
    Resolve a category name to a list of company dicts.
    Dynamic categories read existing intel files to find matches.
    Fixed/thematic categories use hardcoded lists.
    Returns list sliced to count.
    """
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    companies: List[Dict[str, Any]] = []

    if category == "nifty50":
        companies = list(NIFTY50_TICKERS)
    elif category == "budget_impacted":
        companies = list(BUDGET_IMPACTED)
    elif category == "war_impacted":
        companies = list(WAR_IMPACTED)
    elif category == "ai_impacted":
        companies = list(AI_IMPACTED)
    elif category == "dollar_appreciation":
        companies = list(DOLLAR_APPRECIATION)
    elif category == "electric_vehicle":
        companies = list(EV_IMPACTED)
    elif category == "ipo_recent":
        companies = list(RECENT_IPOS)
    elif category == "news_impacted":
        companies = _get_news_impacted(date_str)
    elif category == "quarter_results":
        companies = _get_quarter_results_companies(date_str)
    elif category == "earnings_beat":
        companies = _get_earnings_beat_companies(date_str)
    elif category == "fii_active":
        companies = _get_fii_active_companies(date_str)
    elif category == "high_volatile":
        companies = _get_high_volatile_companies(date_str)
    elif category == "sector_rotation":
        companies = _get_sector_rotation_companies(date_str)
    elif category == "breakout_watch":
        companies = _get_breakout_watch_companies(date_str)
    elif category == "near_52w_high":
        companies = _get_near_52w_high_companies(date_str)
    elif category == "operator_activity":
        companies = _get_unusual_activity_companies(date_str)
    else:
        companies = list(NIFTY50_TICKERS)

    seen = set()
    deduped: List[Dict[str, Any]] = []
    for company in companies:
        ticker = company.get("ticker", "")
        if ticker and ticker not in seen:
            seen.add(ticker)
            deduped.append(company)

    return deduped[:count] if deduped else list(NIFTY50_TICKERS)[:count]


def _load_intel_files(date_str: str) -> list:
    intel_list: List[Dict[str, Any]] = []
    if not os.path.exists(INTEL_DIR):
        return intel_list
    for filename in os.listdir(INTEL_DIR):
        if date_str in filename and filename.endswith(".json"):
            try:
                with open(os.path.join(INTEL_DIR, filename)) as f:
                    intel_list.append(json.load(f))
            except Exception:
                continue
    return intel_list


def _get_news_impacted(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        if intel.get("intraday_relevance") == "HIGH":
            companies.append(
                {
                    "ticker": intel.get("ticker"),
                    "name": intel.get("company_name", intel.get("ticker")),
                    "sector": intel.get("sector_code", "Unknown"),
                    "reason": (intel.get("catalyst_summary") or "")[:80],
                }
            )
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def _get_quarter_results_companies(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        earnings = intel.get("earnings", {}) or {}
        if earnings.get("announced") or intel.get("in_results_window"):
            companies.append(
                {
                    "ticker": intel.get("ticker"),
                    "name": intel.get("company_name", intel.get("ticker")),
                    "sector": intel.get("sector_code", "Unknown"),
                    "eps_surprise": earnings.get("eps_surprise_pct"),
                }
            )
    companies.sort(key=lambda x: abs(x.get("eps_surprise") or 0), reverse=True)
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def _get_earnings_beat_companies(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        surprise = (intel.get("earnings", {}) or {}).get("eps_surprise_pct")
        if surprise is not None and surprise > 5:
            companies.append(
                {
                    "ticker": intel.get("ticker"),
                    "name": intel.get("company_name", intel.get("ticker")),
                    "sector": intel.get("sector_code", "Unknown"),
                    "eps_surprise": surprise,
                }
            )
    companies.sort(key=lambda x: x.get("eps_surprise") or 0, reverse=True)
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def _get_fii_active_companies(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        fii = intel.get("fii_activity", "neutral")
        if fii in ("net_buyer", "net_seller"):
            companies.append(
                {
                    "ticker": intel.get("ticker"),
                    "name": intel.get("company_name", intel.get("ticker")),
                    "sector": intel.get("sector_code", "Unknown"),
                    "fii": fii,
                }
            )
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def _get_high_volatile_companies(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        ohlcv = intel.get("ohlcv", {}) or {}
        day_high = ohlcv.get("day_high")
        day_low = ohlcv.get("day_low")
        if day_high and day_low and day_low > 0:
            range_pct = ((day_high - day_low) / day_low) * 100
            if range_pct > 2.0:
                companies.append(
                    {
                        "ticker": intel.get("ticker"),
                        "name": intel.get("company_name", intel.get("ticker")),
                        "sector": intel.get("sector_code", "Unknown"),
                        "range_pct": round(range_pct, 2),
                    }
                )
    companies.sort(key=lambda x: x.get("range_pct") or 0, reverse=True)
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def _get_sector_rotation_companies(date_str: str) -> list:
    try:
        scores_file = os.path.join(SCORES_DIR, f"trading_scores_{date_str}.json")
        if not os.path.exists(scores_file):
            return list(NIFTY50_TICKERS)[:20]
        with open(scores_file) as f:
            scores_data = json.load(f)
        theme_scores = scores_data.get("theme_scores", [])
        if not theme_scores:
            return list(NIFTY50_TICKERS)[:20]
        top_sector = theme_scores[0].get("sector")
        return [c for c in NIFTY50_TICKERS if c.get("sector") == top_sector] or list(
            NIFTY50_TICKERS
        )[:20]
    except Exception:
        return list(NIFTY50_TICKERS)[:20]


def _get_breakout_watch_companies(date_str: str) -> list:
    try:
        scores_file = os.path.join(SCORES_DIR, f"trading_scores_{date_str}.json")
        if not os.path.exists(scores_file):
            return list(NIFTY50_TICKERS)[:20]
        with open(scores_file) as f:
            scores_data = json.load(f)
        all_scores = scores_data.get("all_scores", [])
        tickers = [s.get("ticker") for s in all_scores if 50 <= (s.get("buy_score") or 0) <= 70]
        return [c for c in NIFTY50_TICKERS if c.get("ticker") in tickers] or list(
            NIFTY50_TICKERS
        )[:20]
    except Exception:
        return list(NIFTY50_TICKERS)[:20]


def _get_near_52w_high_companies(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        fund = intel.get("fundamentals", {}) or {}
        pct = fund.get("week52_high_pct")
        if pct is not None and 0 <= pct <= 5:
            companies.append(
                {
                    "ticker": intel.get("ticker"),
                    "name": intel.get("company_name", intel.get("ticker")),
                    "sector": intel.get("sector_code", "Unknown"),
                    "pct_away": pct,
                }
            )
    companies.sort(key=lambda x: x.get("pct_away") or 99)
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def _get_unusual_activity_companies(date_str: str) -> list:
    intel_list = _load_intel_files(date_str)
    companies: List[Dict[str, Any]] = []
    for intel in intel_list:
        ohlcv = intel.get("ohlcv", {}) or {}
        vol = ohlcv.get("volume") or 0
        avg_vol = (intel.get("fundamentals", {}) or {}).get("avg_volume_10d") or 0
        relevance = intel.get("intraday_relevance", "LOW")
        if avg_vol and vol:
            vol_ratio = vol / avg_vol
            if vol_ratio > 2.5 and relevance == "LOW":
                companies.append(
                    {
                        "ticker": intel.get("ticker"),
                        "name": intel.get("company_name", intel.get("ticker")),
                        "sector": intel.get("sector_code", "Unknown"),
                        "vol_ratio": round(vol_ratio, 1),
                    }
                )
    companies.sort(key=lambda x: x.get("vol_ratio") or 0, reverse=True)
    return companies if companies else list(NIFTY50_TICKERS)[:20]


def run_smart_scan(
    category: str,
    count: int,
    save_as_default: bool = False,
    tenant_id: str = "0001",
) -> Generator[dict, None, None]:
    """
    Run full pipeline for resolved company list.
    Yields progress update dicts as each company is processed.
    """
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    companies = resolve_category(category, count, date_str)
    total = len(companies)

    profile = load_profile()
    profile["last_category"] = category
    profile["last_count"] = count
    profile["last_run_at"] = datetime.datetime.now().isoformat()
    if save_as_default:
        profile["default_category"] = category
        profile["default_count"] = count

    profile.setdefault("run_history", [])
    profile["run_history"].append(
        {
            "category": category,
            "count": count,
            "date": date_str,
            "ran_at": datetime.datetime.now().isoformat(),
        }
    )
    profile["run_history"] = profile["run_history"][-20:]
    save_profile(profile)

    yield {
        "type": "start",
        "total": total,
        "category": category,
        "count": count,
        "companies": [c.get("ticker") for c in companies],
    }

    from backend.layers.layer1_news import run_layer1_news  # noqa: E402
    from backend.layers.layer1_merge import merge_financial_data  # noqa: E402
    from backend.layers.layer2_runner import run_layer2  # noqa: E402

    for i, company in enumerate(companies, 1):
        ticker = company.get("ticker")
        name = company.get("name") or ticker
        sector = company.get("sector", "Unknown")
        yield {
            "type": "progress",
            "step": "news",
            "current": i,
            "total": total,
            "ticker": ticker,
            "message": f"Fetching news for {ticker}...",
            "pct": int((i - 1) / max(total, 1) * 40),
        }
        try:
            if ticker:
                run_layer1_news(ticker, name, sector, verbose=False)
        except Exception as e:
            yield {"type": "warning", "ticker": ticker, "message": f"News failed: {str(e)[:120]}"}
        time.sleep(1.2)

    for i, company in enumerate(companies, 1):
        ticker = company.get("ticker")
        yield {
            "type": "progress",
            "step": "financials",
            "current": i,
            "total": total,
            "ticker": ticker,
            "message": f"Fetching financials for {ticker}...",
            "pct": 40 + int((i - 1) / max(total, 1) * 40),
        }
        try:
            if ticker:
                merge_financial_data(ticker, tenant_id=tenant_id, verbose=False)
        except Exception as e:
            yield {
                "type": "warning",
                "ticker": ticker,
                "message": f"Financials failed: {str(e)[:120]}",
            }
        time.sleep(0.8)

    yield {
        "type": "progress",
        "step": "scoring",
        "current": total,
        "total": total,
        "ticker": "ALL",
        "message": "Running scoring engine...",
        "pct": 85,
    }

    try:
        scores = run_layer2(date_str=date_str, save_to_db=True, verbose=False)
        top_buy = (scores.get("company_scores") or [])[:5]
        top_short = (scores.get("short_scores") or [])[:5]
        yield {
            "type": "complete",
            "pct": 100,
            "date": date_str,
            "category": category,
            "count": total,
            "top_buy": top_buy,
            "top_short": top_short,
            "above_threshold": scores.get("above_threshold", 0),
            "regime": scores.get("regime", ""),
            "message": f"Scan complete. {scores.get('above_threshold', 0)} signals found.",
        }
    except Exception as e:
        yield {"type": "error", "message": f"Scoring failed: {str(e)}"}

