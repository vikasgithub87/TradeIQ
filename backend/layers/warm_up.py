"""
warm_up.py — Tracks observed trading days for Learn Mode gate.
The warm-up gate requires 5 real market days of observation
before Learn Mode can place paper trades. This file tracks
and exposes that counter.
"""

import datetime
import json
import os

WARMUP_FILE = "backend/data/warm_up_state.json"
REQUIRED_DAYS = 5


def load_warmup_state() -> dict:
    """Load warm-up state from disk."""
    try:
        if os.path.exists(WARMUP_FILE):
            with open(WARMUP_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "observed_days": 0,
        "observed_dates": [],
        "gate_unlocked": False,
        "first_observed_date": None,
        "last_observed_date": None,
        "required_days": REQUIRED_DAYS,
    }


def save_warmup_state(state: dict) -> None:
    """Save warm-up state to disk."""
    try:
        os.makedirs("backend/data", exist_ok=True)
        with open(WARMUP_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def record_observation(date_str: str = None) -> dict:
    """
    Record that today is a real observed market day.
    Called by Layer 0 every time it runs on a market-open day.
    Increments observed_days counter. Unlocks gate at 5 days.
    Returns updated state.
    """
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    state = load_warmup_state()

    if date_str in state.get("observed_dates", []):
        state["days_remaining"] = max(0, REQUIRED_DAYS - state.get("observed_days", 0))
        state["pct_complete"] = min(
            100, int(state.get("observed_days", 0) / REQUIRED_DAYS * 100)
        )
        return state

    state.setdefault("observed_dates", [])
    state["observed_dates"].append(date_str)
    state["observed_dates"] = sorted(state["observed_dates"])[-30:]

    state["observed_days"] = len(state["observed_dates"])
    state["last_observed_date"] = date_str
    if state.get("first_observed_date") is None:
        state["first_observed_date"] = date_str

    state["gate_unlocked"] = state["observed_days"] >= REQUIRED_DAYS
    state["required_days"] = REQUIRED_DAYS
    state["days_remaining"] = max(0, REQUIRED_DAYS - state["observed_days"])
    state["pct_complete"] = min(
        100, int(state.get("observed_days", 0) / REQUIRED_DAYS * 100)
    )

    save_warmup_state(state)
    return state


def get_warmup_status() -> dict:
    """
    Return current warm-up status.
    Used by Learn Mode gate and the dashboard settings panel.
    """
    state = load_warmup_state()
    state["required_days"] = REQUIRED_DAYS
    state["days_remaining"] = max(0, REQUIRED_DAYS - state.get("observed_days", 0))
    state["pct_complete"] = min(
        100, int(state.get("observed_days", 0) / REQUIRED_DAYS * 100)
    )
    return state


def is_gate_unlocked() -> bool:
    """Quick boolean check — used by Sprint 11 Learn Mode."""
    return load_warmup_state().get("gate_unlocked", False)


def reset_warmup(confirm: bool = False) -> None:
    """
    Reset warm-up counter. Requires confirm=True.
    Used for testing only — dangerous in production.
    """
    if not confirm:
        print("Pass confirm=True to reset warm-up state.")
        return
    save_warmup_state(
        {
            "observed_days": 0,
            "observed_dates": [],
            "gate_unlocked": False,
            "first_observed_date": None,
            "last_observed_date": None,
            "required_days": REQUIRED_DAYS,
            "days_remaining": REQUIRED_DAYS,
            "pct_complete": 0,
        }
    )
    print("Warm-up state reset.")


if __name__ == "__main__":
    import sys

    if "--status" in sys.argv:
        status = get_warmup_status()
        print("\nWarm-up Gate Status")
        print("=" * 40)
        print(f"Observed days:   {status['observed_days']}/{REQUIRED_DAYS}")
        print(f"Days remaining:  {status['days_remaining']}")
        print(f"Gate unlocked:   {status['gate_unlocked']}")
        print(f"Progress:        {status['pct_complete']}%")
        if status.get("observed_dates"):
            print(f"Dates observed:  {', '.join(status['observed_dates'])}")
    elif "--reset" in sys.argv:
        reset_warmup(confirm=True)
    elif "--record" in sys.argv:
        date = (
            sys.argv[sys.argv.index("--record") + 1]
            if "--record" in sys.argv and len(sys.argv) > sys.argv.index("--record") + 1
            else None
        )
        state = record_observation(date)
        print(f"Recorded. Observed days: {state['observed_days']}/{REQUIRED_DAYS}")
        print(f"Gate unlocked: {state['gate_unlocked']}")
    else:
        print("Usage:")
        print("  python backend/layers/warm_up.py --status")
        print("  python backend/layers/warm_up.py --record 2025-03-15")
        print("  python backend/layers/warm_up.py --reset")

