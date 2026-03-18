"""
layer2_velocity.py — Tracks daily score changes per company.
"""
import os
import json
import datetime
from typing import Optional, Dict, Any

VELOCITY_FILE = "backend/data/score_velocity.json"


def load_velocity_history() -> Dict[str, Any]:
    try:
        if os.path.exists(VELOCITY_FILE):
            with open(VELOCITY_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_velocity_history(history: Dict[str, Any]) -> None:
    try:
        os.makedirs("backend/data", exist_ok=True)
        with open(VELOCITY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass


def calculate_velocity(
    ticker: str,
    today_score: float,
    history: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if history is None:
        history = load_velocity_history()

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    ticker_hist = history.get(ticker, [])

    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    yesterday_score = None
    for entry in reversed(ticker_hist):
        if entry.get("date") == yesterday_str:
            yesterday_score = entry.get("score")
            break
    if yesterday_score is None and ticker_hist:
        yesterday_score = ticker_hist[-1].get("score")

    delta = round(today_score - yesterday_score, 1) if yesterday_score is not None else 0.0

    if delta >= 20:
        velocity_label = "surging"
    elif delta >= 10:
        velocity_label = "rising_fast"
    elif delta >= 5:
        velocity_label = "rising"
    elif delta >= -5:
        velocity_label = "stable"
    elif delta >= -10:
        velocity_label = "falling"
    else:
        velocity_label = "dropping"

    streak = 0
    for entry in reversed(ticker_hist):
        if entry.get("score", 0) >= 60:
            streak += 1
        else:
            break

    return {
        "ticker": ticker,
        "today_score": today_score,
        "yesterday_score": yesterday_score,
        "delta": delta,
        "velocity_label": velocity_label,
        "streak_days": streak,
        "is_breakout": delta >= 15 and today_score >= 65,
    }


def update_velocity_history(ticker: str, score: float, history: Dict[str, Any]) -> Dict[str, Any]:
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    ticker_hist = history.get(ticker, [])
    ticker_hist = [e for e in ticker_hist if e.get("date") != today_str]
    ticker_hist.append({"date": today_str, "score": score})
    ticker_hist = sorted(ticker_hist, key=lambda x: x["date"])[-30:]
    history[ticker] = ticker_hist
    return history

