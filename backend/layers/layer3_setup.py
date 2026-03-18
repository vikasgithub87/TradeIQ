"""
layer3_setup.py — Precise trade setup generator for NSE intraday.
Calculates entry range, targets, and ATR-based stop loss.
Handles both BUY (long) and SHORT (inverted) setups correctly.
"""
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# ATR multipliers by regime
ATR_MULTIPLIERS = {
    "TRENDING_BULL": 1.2,
    "TRENDING_BEAR": 1.3,
    "RANGE_BOUND": 1.4,
    "HIGH_VOLATILITY": 1.8,
    "EXPIRY_CAUTION": 1.6,
    "DO_NOT_TRADE": 2.0,
}


def generate_buy_setup(
    current_price: float,
    atr: float,
    levels: dict,
    indicators: dict,
    regime: str,
) -> dict:
    """
    Generate BUY trade setup with entry range, targets, and stop loss.
    Entry is above current price near nearest resistance.
    Stop is below entry using ATR multiplier.
    """
    atr_mult = ATR_MULTIPLIERS.get(regime, 1.4)

    entry_low = round(current_price * 1.001, 2)
    entry_high = round(current_price * 1.003, 2)

    stop_loss = round(entry_low - (atr * atr_mult), 2)
    sl_pct = round(((entry_low - stop_loss) / entry_low) * 100, 2)

    pdl = levels.get("pdl")
    if pdl and pdl > stop_loss and pdl < entry_low:
        stop_loss = round(pdl * 0.998, 2)
        sl_pct = round(((entry_low - stop_loss) / entry_low) * 100, 2)

    resistance_levels = levels.get("resistance_levels", [])
    nearest_res = levels.get("nearest_resistance")
    if nearest_res and nearest_res > entry_high:
        target1 = round(nearest_res * 0.998, 2)
    else:
        target1 = round(entry_low + (atr * atr_mult * 2), 2)

    if len(resistance_levels) >= 2:
        target2 = round(resistance_levels[1] * 0.998, 2)
    else:
        target2 = round(entry_low + (atr * atr_mult * 3.5), 2)

    reward = target1 - entry_low
    risk = entry_low - stop_loss
    rr = round(reward / risk, 2) if risk > 0 else 0
    exp_move_pct = round((target1 - entry_low) / entry_low * 100, 2)

    return {
        "direction": "BUY",
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "sl_pct": sl_pct,
        "target_1": target1,
        "target_2": target2,
        "risk_reward": rr,
        "expected_move_pct": exp_move_pct,
        "atr": round(atr, 2),
        "atr_multiplier": atr_mult,
        "invalidation": f"Trade invalid if price closes below ₹{stop_loss}",
    }


def generate_short_setup(
    current_price: float,
    atr: float,
    levels: dict,
    indicators: dict,
    regime: str,
) -> dict:
    """
    Generate SHORT trade setup. Logic is INVERTED from BUY.
    Entry is below current price. Stop is ABOVE entry.
    Target is below entry. Sell first, buy back lower.
    """
    atr_mult = ATR_MULTIPLIERS.get(regime, 1.4)
    atr_mult = round(atr_mult * 1.1, 2)

    entry_high = round(current_price * 0.999, 2)
    entry_low = round(current_price * 0.997, 2)

    stop_loss = round(entry_high + (atr * atr_mult), 2)
    sl_pct = round(((stop_loss - entry_high) / entry_high) * 100, 2)

    pdh = levels.get("pdh")
    if pdh and pdh < stop_loss and pdh > entry_high:
        stop_loss = round(pdh * 1.002, 2)
        sl_pct = round(((stop_loss - entry_high) / entry_high) * 100, 2)

    support_levels = levels.get("support_levels", [])
    nearest_sup = levels.get("nearest_support")
    if nearest_sup and nearest_sup < entry_low:
        target1 = round(nearest_sup * 1.002, 2)
    else:
        target1 = round(entry_high - (atr * atr_mult * 2), 2)

    if len(support_levels) >= 2:
        target2 = round(support_levels[1] * 1.002, 2)
    else:
        target2 = round(entry_high - (atr * atr_mult * 3.5), 2)

    reward = entry_high - target1
    risk = stop_loss - entry_high
    rr = round(reward / risk, 2) if risk > 0 else 0
    exp_move_pct = round((entry_high - target1) / entry_high * 100, 2)

    return {
        "direction": "SHORT",
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "sl_pct": sl_pct,
        "target_1": target1,
        "target_2": target2,
        "risk_reward": rr,
        "expected_move_pct": exp_move_pct,
        "atr": round(atr, 2),
        "atr_multiplier": atr_mult,
        "short_note": "SELL first at entry, BUY BACK at target",
        "invalidation": f"Trade invalid if price closes above ₹{stop_loss}",
    }


def generate_trade_setup(
    direction: str,
    current_price: float,
    atr: Optional[float],
    levels: dict,
    indicators: dict,
    regime: str,
) -> Optional[dict]:
    """
    Main entry point. Routes to BUY or SHORT setup generator.
    Returns None if ATR unavailable or price is invalid.
    """
    if not current_price or current_price <= 0:
        return None
    if not atr or atr <= 0:
        atr = round(current_price * 0.015, 2)

    if direction == "BUY":
        return generate_buy_setup(current_price, atr, levels, indicators, regime)
    if direction == "SHORT":
        return generate_short_setup(current_price, atr, levels, indicators, regime)
    return None

