"""
layer0.py — TradeIQ Layer 0: Market Regime DNA Classifier
Runs every morning at 07:30 IST.
Determines the market state and sets thresholds for all downstream layers.

Usage:
    python backend/layers/layer0.py                    # run for today
    python backend/layers/layer0.py --date 2025-03-15  # run for specific date
    python backend/layers/layer0.py --mock-vix 29.5    # test with mock VIX
"""
import os
import sys
import json
import argparse
import datetime
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from backend.layers.layer0_calendar import check_calendar
from backend.layers.layer0_macro import get_macro_snapshot

DATA_DIR        = str(_ROOT / "backend" / "data")
REGIME_FILE     = str(_ROOT / "backend" / "data" / "regime_context.json")
HISTORY_FILE    = str(_ROOT / "backend" / "data" / "regime_history.json")
TENANT_ID       = "0001"   # Personal use tenant

# ── Regime Thresholds ─────────────────────────────────────────────────────────
REGIME_THRESHOLDS = {
    "DO_NOT_TRADE":   {"l2": 999, "conf": 999, "pos_mult": 0.0, "directions": []},
    "EXPIRY_CAUTION": {"l2": 80,  "conf": 78,  "pos_mult": 0.6, "directions": ["BUY", "SHORT"]},
    "HIGH_VOLATILITY":{"l2": 78,  "conf": 75,  "pos_mult": 0.5, "directions": ["BUY", "SHORT"]},
    "RANGE_BOUND":    {"l2": 72,  "conf": 70,  "pos_mult": 0.8, "directions": ["BUY", "SHORT"]},
    "TRENDING_BEAR":  {"l2": 60,  "conf": 60,  "pos_mult": 1.0, "directions": ["SHORT"]},
    "TRENDING_BULL":  {"l2": 60,  "conf": 60,  "pos_mult": 1.0, "directions": ["BUY", "SHORT"]},
}

# ── Regime Score Weights ──────────────────────────────────────────────────────
def compute_regime_score(vix: float, calendar: dict, macro: dict) -> int:
    """
    Compute a 0-100 regime health score.
    Higher = better conditions for intraday momentum trading.
    """
    score = 60  # baseline neutral

    # VIX contribution (lower VIX = better conditions)
    if vix < 12:
        score += 20
    elif vix < 15:
        score += 12
    elif vix < 18:
        score += 5
    elif vix < 22:
        score -= 5
    elif vix < 26:
        score -= 15
    else:
        score -= 30

    # Calendar contribution
    if calendar["is_monthly_expiry"]:
        score -= 10
    elif calendar["is_weekly_expiry"]:
        score -= 5
    if calendar["is_rbi_day"]:
        score -= 20
    if calendar["is_budget_day"]:
        score -= 25
    if calendar["days_to_expiry"] <= 2:
        score -= 5   # Expiry week caution

    # Global macro contribution
    if macro.get("global_sentiment") == "positive":
        score += 8
    elif macro.get("global_sentiment") == "negative":
        score -= 8

    sp500 = macro.get("sp500_futures")
    if sp500:
        if sp500["change_pct"] > 1.0:
            score += 5
        elif sp500["change_pct"] < -1.0:
            score -= 8

    crude = macro.get("crude_oil_usd")
    if crude:
        if crude > 95:
            score -= 6
        elif crude < 75:
            score += 4

    return max(0, min(100, score))

def classify_regime(
    date_str: str = None,
    mock_vix: float = None
) -> dict:
    """
    Main regime classification function.
    Returns the complete regime context dict and saves it to disk.
    """
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    print(f"\nTradeIQ Layer 0 — Market Regime DNA")
    print(f"Date: {date_str}")
    print("=" * 50)

    # Step 1 — Calendar check
    print("Step 1: Checking calendar...")
    calendar = check_calendar(date_str)

    if not calendar["market_open"]:
        reason = calendar.get("holiday_name") or "Weekend"
        print(f"  Market closed: {reason}")
        result = _build_closed_regime(date_str, reason, calendar)
        result["warmup_observed_days"] = None
        result["warmup_gate_unlocked"] = False
        result["warmup_days_remaining"] = None
        _save_regime(result)
        _print_morning_briefing(result, calendar, {})
        return result

    print(f"  Market open. Expiry day: {calendar['is_expiry_day']}")
    print(f"  RBI day: {calendar['is_rbi_day']}  Budget day: {calendar['is_budget_day']}")

    # Step 2 — Macro snapshot
    print("Step 2: Fetching global macro data...")
    macro = get_macro_snapshot(mock_vix=mock_vix)
    vix   = macro["india_vix"]
    print(f"  India VIX: {vix}")
    if macro.get("crude_oil_usd"):
        print(f"  Crude oil: ${macro['crude_oil_usd']}")
    if macro.get("sp500_futures"):
        sp = macro["sp500_futures"]
        print(f"  S&P 500 futures: {sp['change_pct']:+.2f}%  ({sp['direction']})")

    # Step 3 — Classify regime (priority order)
    print("Step 3: Classifying regime...")

    if calendar["is_budget_day"]:
        regime = "DO_NOT_TRADE"
        reason = "Union Budget day — extreme volatility, no intraday edge"

    elif calendar["is_rbi_day"]:
        regime = "DO_NOT_TRADE"
        reason = "RBI MPC announcement day — rate decision volatility"

    elif vix > 28:
        regime = "DO_NOT_TRADE"
        reason = f"India VIX at {vix} — market fear extreme, avoid all positions"

    elif vix > 22 or (macro.get("sp500_futures") and
                      macro["sp500_futures"]["change_pct"] < -1.5):
        regime = "HIGH_VOLATILITY"
        reason = (f"VIX elevated at {vix}" if vix > 22
                  else "S&P 500 futures down sharply overnight")

    elif calendar["is_monthly_expiry"]:
        regime = "EXPIRY_CAUTION"
        reason = "Monthly F&O expiry — pin risk and artificial moves near strikes"

    elif calendar["is_weekly_expiry"] and vix > 18:
        regime = "EXPIRY_CAUTION"
        reason = f"Weekly expiry + elevated VIX {vix} — reduce position size"

    else:
        # Determine trend direction from macro
        sp500 = macro.get("sp500_futures")
        crude = macro.get("crude_oil_usd")
        bull_signals = 0
        bear_signals = 0

        if sp500:
            if sp500["change_pct"] > 0.5:
                bull_signals += 2
            elif sp500["change_pct"] < -0.5:
                bear_signals += 2

        if vix < 13:
            bull_signals += 2
        elif vix < 16:
            bull_signals += 1
        elif vix > 20:
            bear_signals += 1

        if crude and crude > 92:
            bear_signals += 1

        if bull_signals > bear_signals + 1:
            regime = "TRENDING_BULL"
            reason = f"Low VIX ({vix}), positive global cues — momentum conditions good"
        elif bear_signals > bull_signals + 1:
            regime = "TRENDING_BEAR"
            reason = f"Negative global cues, VIX rising — short-side conditions active"
        else:
            regime = "RANGE_BOUND"
            reason = f"Mixed signals — VIX {vix}, no clear directional bias"

    print(f"  Regime: {regime}")

    # Step 4 — Get thresholds
    thresholds = REGIME_THRESHOLDS[regime]

    # Step 5 — Compute regime score
    regime_score = compute_regime_score(vix, calendar, macro)
    if regime == "DO_NOT_TRADE":
        regime_score = 0

    # Step 6 — Build result
    result = {
        "date":                    date_str,
        "tenant_id":               TENANT_ID,
        "market_open":             True,
        "regime":                  regime,
        "regime_score":            regime_score,
        "do_not_trade":            regime == "DO_NOT_TRADE",
        "india_vix":               vix,
        "nifty50":                 macro.get("nifty50"),
        "nifty50_chg_pct":         macro.get("nifty50_chg_pct"),
        "banknifty":               macro.get("banknifty"),
        "banknifty_chg_pct":       macro.get("banknifty_chg_pct"),
        "nifty_direction":         macro.get("nifty_direction", "flat"),
        "crude_oil_usd":           macro.get("crude_oil_usd"),
        "dollar_index":            macro.get("dollar_index"),
        "sp500_futures":           macro.get("sp500_futures"),
        "global_sentiment":        macro.get("global_sentiment"),
        "is_expiry_day":           calendar["is_expiry_day"],
        "is_monthly_expiry":       calendar["is_monthly_expiry"],
        "is_weekly_expiry":        calendar["is_weekly_expiry"],
        "is_rbi_day":              calendar["is_rbi_day"],
        "is_budget_day":           calendar["is_budget_day"],
        "days_to_expiry":          calendar["days_to_expiry"],
        "monthly_expiry_date":     calendar["monthly_expiry_date"],
        "signal_threshold_l2":     thresholds["l2"],
        "signal_threshold_conf":   thresholds["conf"],
        "position_size_multiplier":thresholds["pos_mult"],
        "allowed_directions":      thresholds["directions"],
        "regime_reason":           reason,
        "generated_at":            datetime.datetime.now().isoformat(),
    }

    # Step 7 — Save and print
    _save_regime(result)
    from backend.layers.warm_up import record_observation
    if result.get("market_open") and not result.get("do_not_trade"):
        warmup = record_observation(date_str)
        result["warmup_observed_days"] = warmup.get("observed_days", 0)
        result["warmup_gate_unlocked"] = warmup.get("gate_unlocked", False)
        result["warmup_days_remaining"] = warmup.get("days_remaining", 5)
    else:
        result["warmup_observed_days"] = None
        result["warmup_gate_unlocked"] = False
        result["warmup_days_remaining"] = None
    _save_regime(result)
    _update_history(result)
    _print_morning_briefing(result, calendar, macro)

    return result

def _build_closed_regime(date_str: str, reason: str, calendar: dict) -> dict:
    """Build a regime context dict for a market-closed day."""
    return {
        "date":                    date_str,
        "tenant_id":               TENANT_ID,
        "market_open":             False,
        "regime":                  "MARKET_CLOSED",
        "regime_score":            0,
        "do_not_trade":            True,
        "india_vix":               None,
        "crude_oil_usd":           None,
        "dollar_index":            None,
        "sp500_futures":           None,
        "global_sentiment":        "neutral",
        "is_expiry_day":           False,
        "is_monthly_expiry":       False,
        "is_weekly_expiry":        False,
        "is_rbi_day":              calendar.get("is_rbi_day", False),
        "is_budget_day":           calendar.get("is_budget_day", False),
        "days_to_expiry":          calendar.get("days_to_expiry", 0),
        "monthly_expiry_date":     calendar.get("monthly_expiry_date", ""),
        "signal_threshold_l2":     999,
        "signal_threshold_conf":   999,
        "position_size_multiplier":0.0,
        "allowed_directions":      [],
        "regime_reason":           f"Market closed: {reason}",
        "generated_at":            datetime.datetime.now().isoformat(),
    }

def _save_regime(result: dict):
    """Save regime context to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REGIME_FILE, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Saved: {REGIME_FILE}")

def _update_history(result: dict):
    """Append today's regime to history file for analytics."""
    os.makedirs(DATA_DIR, exist_ok=True)
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                history = json.load(f)
        except Exception:
            history = []

    # Remove existing entry for this date if any
    history = [h for h in history if h.get("date") != result["date"]]

    # Append compact summary
    history.append({
        "date":         result["date"],
        "regime":       result["regime"],
        "regime_score": result["regime_score"],
        "vix":          result["india_vix"],
        "do_not_trade": result["do_not_trade"],
        "is_expiry":    result["is_expiry_day"],
        "is_rbi":       result["is_rbi_day"],
    })

    # Keep last 365 days
    history = sorted(history, key=lambda x: x["date"])[-365:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def _print_morning_briefing(result: dict, calendar: dict, macro: dict):
    """
    Print a clean morning briefing to the terminal.
    Readable in 10 seconds — like a market newspaper headline.
    """
    print("\n" + "=" * 60)
    print("  TRADEIQ MORNING BRIEFING")
    print(f"  {result['date']}")
    print("=" * 60)

    if not result["market_open"]:
        print(f"  MARKET CLOSED — {result['regime_reason']}")
        print("=" * 60)
        return

    # Regime status (ASCII-safe for Windows console)
    regime_display = {
        "TRENDING_BULL":   "TRENDING BULL   ^  Full signals active",
        "TRENDING_BEAR":   "TRENDING BEAR   v  Short signals active",
        "RANGE_BOUND":     "RANGE BOUND     -  Tighter thresholds",
        "HIGH_VOLATILITY": "HIGH VOLATILITY *  Reduced position size",
        "EXPIRY_CAUTION":  "EXPIRY CAUTION  !  Expiry day - reduce size",
        "DO_NOT_TRADE":    "DO NOT TRADE    X  Stay out today",
    }
    print(f"\n  REGIME:  {regime_display.get(result['regime'], result['regime'])}")
    print(f"  SCORE:   {result['regime_score']}/100")
    print(f"  REASON:  {result['regime_reason']}")

    # Market data
    print("\n  MARKET DATA:")
    print(f"    India VIX:       {result.get('india_vix', 'N/A')}")
    if result.get("crude_oil_usd"):
        print(f"    Crude Oil:       ${result['crude_oil_usd']}/bbl")
    if result.get("dollar_index"):
        print(f"    Dollar Index:    {result['dollar_index']}")
    sp = result.get("sp500_futures")
    if sp:
        print(f"    S&P 500 Futures: {sp['change_pct']:+.2f}%  ({sp['direction']})")

    # Today's flags
    flags = []
    if result["is_monthly_expiry"]:
        flags.append("Monthly F&O Expiry")
    elif result["is_weekly_expiry"]:
        flags.append("Weekly Options Expiry")
    if result["is_rbi_day"]:
        flags.append("RBI Policy Day")
    if result["is_budget_day"]:
        flags.append("Union Budget Day")
    if flags:
        print(f"\n  TODAY'S FLAGS:  {' | '.join(flags)}")

    # Trading parameters
    if not result["do_not_trade"]:
        print(f"\n  TRADING PARAMETERS:")
        print(f"    L2 Score threshold:   >= {result['signal_threshold_l2']}")
        print(f"    Confidence threshold: >= {result['signal_threshold_conf']}")
        print(f"    Position size:        {int(result['position_size_multiplier'] * 100)}% of normal")
        print(f"    Active directions:    {', '.join(result['allowed_directions'])}")
        print(f"    Days to expiry:       {result['days_to_expiry']}")
    else:
        print("\n  [!] NO TRADES TODAY - All signals suppressed")

    print("\n" + "=" * 60)

# ── CLI Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TradeIQ Layer 0 — Market Regime DNA")
    parser.add_argument("--date",     type=str,   default=None,
                        help="Date to classify (YYYY-MM-DD). Default: today.")
    parser.add_argument("--mock-vix", type=float, default=None,
                        help="Override VIX with a test value (e.g. 29.5).")
    args = parser.parse_args()
    classify_regime(date_str=args.date, mock_vix=args.mock_vix)
