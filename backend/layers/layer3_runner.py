"""
layer3_runner.py — TradeIQ Layer 3: Technical Validator.
Reads Layer 2 scores, validates each signal with technical analysis,
generates confidence scores and trade setups.

Usage:
    python backend/layers/layer3_runner.py
    python backend/layers/layer3_runner.py --ticker RELIANCE
    python backend/layers/layer3_runner.py --date 2025-03-15
"""
import os
import sys
import json
import datetime
import argparse
import asyncio
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.layers.layer3_indicators import run_all_indicators
from backend.layers.layer3_patterns import detect_patterns
from backend.layers.layer3_levels import get_all_levels
from backend.layers.layer3_confidence import calculate_confidence
from backend.layers.layer3_setup import generate_trade_setup

SCORES_DIR = "backend/data/scores"
INTEL_DIR = "backend/data/company_intel"
SIGNALS_DIR = "backend/data/signals"
REGIME_FILE = "backend/data/regime_context.json"
TENANT_ID = "0001"


def load_regime() -> dict:
    try:
        if os.path.exists(REGIME_FILE):
            with open(REGIME_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "regime": "RANGE_BOUND",
        "signal_threshold_l2": 60,
        "position_size_multiplier": 1.0,
    }


def load_scores(date_str: str) -> dict:
    filepath = os.path.join(SCORES_DIR, f"trading_scores_{date_str}.json")
    if not os.path.exists(filepath):
        return {}
    with open(filepath) as f:
        return json.load(f)


def load_intel(ticker: str, date_str: str) -> dict:
    filename = f"company_intel_{ticker}_{date_str}.json"
    filepath = os.path.join(INTEL_DIR, filename)
    if not os.path.exists(filepath):
        return {}
    with open(filepath) as f:
        return json.load(f)


def validate_signal(
    score: dict,
    intel: dict,
    regime: dict,
    verbose: bool = False,
) -> Optional[dict]:
    """
    Run full Layer 3 technical validation for one company signal.
    Returns validated signal dict or None if insufficient data.
    """
    ticker = score.get("ticker", "")
    direction = score.get("recommended_direction", "LONG")
    if direction == "NEUTRAL":
        return None

    api_direction = "BUY" if direction == "LONG" else "SHORT"
    regime_name = regime.get("regime", "RANGE_BOUND")
    threshold = regime.get("signal_threshold_l2", 60)

    if verbose:
        print(f"  [{ticker}] Technical validation ({api_direction})...")

    candles = (intel.get("ohlcv") or {}).get("candles", [])

    if not candles:
        try:
            from backend.layers.layer1_financials import fetch_intraday_ohlcv

            ohlcv_data = fetch_intraday_ohlcv(ticker)
            candles = ohlcv_data.get("candles", [])
        except Exception:
            pass

    if not candles or len(candles) < 10:
        if verbose:
            print(f"  [{ticker}] Insufficient candle data — skipping")
        return None

    indicators = run_all_indicators(candles)
    patterns = detect_patterns(candles)
    levels = get_all_levels(ticker, candles)

    if not indicators.get("sufficient_data"):
        if verbose:
            print(f"  [{ticker}] Insufficient indicator data — skipping")
        return None

    l2_score = score.get("buy_score", 0) if api_direction == "BUY" else score.get("short_score", 0)

    confidence = calculate_confidence(
        l2_score=l2_score,
        direction=api_direction,
        indicators=indicators,
        patterns=patterns,
        levels=levels,
        regime=regime_name,
        threshold=threshold,
    )

    atr = indicators.get("atr")
    price = levels.get("current_price")
    setup = generate_trade_setup(
        direction=api_direction,
        current_price=price,
        atr=atr,
        levels=levels,
        indicators=indicators,
        regime=regime_name,
    )

    if not setup:
        return None

    # Invalidation check — has price already hit the stop zone?
    invalidation_triggered = False
    invalidation_note = None

    if setup and candles:
        try:
            recent_candles = candles[-3:]  # last 3 candles
            stop_loss = setup.get("stop_loss", 0)

            if api_direction == "BUY":
                recent_lows = [float(c.get("low", 999999)) for c in recent_candles]
                if any(low <= stop_loss for low in recent_lows):
                    invalidation_triggered = True
                    invalidation_note = (
                        f"⚠ Price recently touched stop zone ₹{stop_loss:.1f} — "
                        f"signal may be invalidated"
                    )
            else:
                recent_highs = [float(c.get("high", 0)) for c in recent_candles]
                if any(high >= stop_loss for high in recent_highs):
                    invalidation_triggered = True
                    invalidation_note = (
                        f"⚠ Price recently touched stop zone ₹{stop_loss:.1f} — "
                        f"short may be invalidated"
                    )
        except Exception:
            pass

    conf_score = confidence["confidence_score"]
    l2_thresh = regime.get("signal_threshold_l2", 60)

    if conf_score >= 80 and l2_score >= l2_thresh + 15:
        final_signal = f"HIGH_CONVICTION_{api_direction}"
    elif conf_score >= 65 and l2_score >= l2_thresh:
        final_signal = f"MODERATE_{api_direction}"
    elif conf_score >= 50:
        final_signal = f"WEAK_{api_direction}"
    else:
        final_signal = "AVOID"

    validated = {
        "ticker": ticker,
        "tenant_id": TENANT_ID,
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "direction": api_direction,
        "l2_score": l2_score,
        "confidence_score": conf_score,
        "final_signal": final_signal,
        "technical_alignment": confidence["technical_alignment"],
        "confluence_score": confidence["confluence"]["confluence_score"],
        "agreeing_signals": confidence["confluence"]["agreeing_signals"],
        "total_signals": confidence["confluence"]["total_signals"],
        "entry_low": setup.get("entry_low"),
        "entry_high": setup.get("entry_high"),
        "target_1": setup.get("target_1"),
        "target_2": setup.get("target_2"),
        "stop_loss": setup.get("stop_loss"),
        "risk_reward": setup.get("risk_reward"),
        "expected_move_pct": setup.get("expected_move_pct"),
        "atr": setup.get("atr"),
        "rsi": indicators.get("rsi"),
        "macd_crossover": (indicators.get("macd") or {}).get("crossover"),
        "ema_trend": (indicators.get("ema") or {}).get("trend"),
        "volume_ratio": (indicators.get("volume") or {}).get("volume_ratio"),
        "vwap": levels.get("vwap"),
        "vwap_position": (levels.get("vwap_position") or {}).get("position"),
        "pdh": levels.get("pdh"),
        "pdl": levels.get("pdl"),
        "pdh_breakout": levels.get("pdh_breakout"),
        "pdl_breakdown": levels.get("pdl_breakdown"),
        "patterns": [p["name"] for p in patterns.get("patterns", [])],
        "dominant_pattern": patterns.get("dominant"),
        "penalty_reasons": confidence.get("penalty_reasons", []),
        "l3_flags": score.get("l3_flags", []),
        "pass_to_trade": final_signal != "AVOID",
        "confidence_breakdown": confidence.get("breakdown", {}),
        "confluence_detail": confidence["confluence"].get("breakdown", []),
        "setup_detail": setup,
        "time_quality": confidence.get("time_quality", 1.0),
        "time_note": confidence.get("time_note"),
        "optimal_entry_window": confidence.get("optimal_entry_window", False),
        "invalidation_triggered": invalidation_triggered,
        "invalidation_note": invalidation_note,
        "generated_at": datetime.datetime.now().isoformat(),
    }

    # 52-week proximity flags from intel file
    fund = intel.get("fundamentals", {}) or {}
    w52h_pct = fund.get("week52_high_pct")
    w52l_pct = fund.get("week52_low_pct")

    validated["week52_high"] = fund.get("week52_high")
    validated["week52_low"] = fund.get("week52_low")
    validated["week52_high_pct"] = w52h_pct
    validated["week52_low_pct"] = w52l_pct
    validated["near_52w_high"] = (w52h_pct is not None and w52h_pct <= 3.0)
    validated["near_52w_low"] = (w52l_pct is not None and w52l_pct <= 5.0)
    validated["exhaustion_risk"] = (
        api_direction == "BUY" and w52h_pct is not None and w52h_pct <= 2.0
    )
    validated["reversal_potential"] = (
        api_direction == "BUY" and w52l_pct is not None and w52l_pct <= 3.0
    )

    # Market cap category
    market_cap_cr = intel.get("market_cap_cr") or 0
    if market_cap_cr >= 50000:
        cap_category = "Large Cap"
    elif market_cap_cr >= 20000:
        cap_category = "Mid Cap"
    elif market_cap_cr >= 5000:
        cap_category = "Small Cap"
    elif market_cap_cr > 0:
        cap_category = "Micro Cap"
    else:
        cap_category = "Unknown"

    validated["market_cap_cr"] = market_cap_cr or None
    validated["cap_category"] = cap_category

    # Reduce confidence if already invalidated
    if invalidation_triggered:
        validated["confidence_score"] = max(0, validated["confidence_score"] - 20)
        if "ALREADY_NEAR_STOP" not in validated.get("penalty_reasons", []):
            validated.setdefault("penalty_reasons", []).append(
                "Price recently touched stop zone"
            )

    if verbose:
        print(
            f"  [{ticker}] Confidence: {conf_score:.0f}  "
            f"Signal: {final_signal}  R:R {setup.get('risk_reward', 0):.1f}"
        )

    return validated


async def save_signals_to_db(signals: list):
    """Save validated signals to PostgreSQL."""
    try:
        from backend.db import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            for sig in signals:
                await session.execute(
                    text(
                        """
                        INSERT INTO validated_signals
                            (id, tenant_id, ticker, date, direction,
                             confidence_score, entry_low, entry_high,
                             target_1, target_2, stop_loss,
                             risk_reward, final_signal, narrative)
                        VALUES
                            (gen_random_uuid(), :tenant_id, :ticker, :date,
                             :direction, :confidence_score, :entry_low,
                             :entry_high, :target_1, :target_2, :stop_loss,
                             :risk_reward, :final_signal, :narrative)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {
                        "tenant_id": TENANT_ID,
                        "ticker": sig["ticker"],
                        "date": sig["date"],
                        "direction": sig["direction"],
                        "confidence_score": sig["confidence_score"],
                        "entry_low": sig["entry_low"],
                        "entry_high": sig["entry_high"],
                        "target_1": sig["target_1"],
                        "target_2": sig["target_2"],
                        "stop_loss": sig["stop_loss"],
                        "risk_reward": sig["risk_reward"],
                        "final_signal": sig["final_signal"],
                        "narrative": "",
                    },
                )
            await session.commit()
    except Exception as e:
        print(f"  WARNING: DB save failed: {e}")


def run_layer3(
    date_str: Optional[str] = None,
    ticker: Optional[str] = None,
    save_to_db: bool = True,
    verbose: bool = True,
) -> dict:
    """Main Layer 3 orchestrator."""
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    if verbose:
        print("\nTradeIQ Layer 3 — Technical Validator")
        print(f"Date: {date_str}")
        print("=" * 60)

    regime = load_regime()
    scores = load_scores(date_str)

    if not scores:
        print("  No Layer 2 scores found. Run layer2_runner.py first.")
        return {}

    if ticker:
        all_scores = scores.get("all_scores", [])
        companies = [s for s in all_scores if s.get("ticker") == ticker.upper()]
    else:
        companies = list(scores.get("company_scores", []) or [])
        short_cands = list(scores.get("short_scores", []) or [])
        seen = {c.get("ticker") for c in companies if c.get("ticker")}
        for s in short_cands:
            t = s.get("ticker")
            if t and t not in seen:
                companies.append(s)
                seen.add(t)

    if verbose:
        print(f"  Validating {len(companies)} companies...")

    # Load sector theme scores for context
    sector_themes = {}
    try:
        for theme in scores.get("theme_scores", []):
            sector_themes[theme["sector"]] = {
                "theme_score": theme.get("theme_score", 0),
                "signal": theme.get("signal", "neutral"),
                "above_threshold": theme.get("above_threshold", 0),
            }
    except Exception:
        pass

    validated_signals = []
    for company in companies:
        t = company.get("ticker", "")
        intel = load_intel(t, date_str)
        try:
            signal = validate_signal(company, intel, regime, verbose)
            if signal:
                # Add sector momentum context
                company_sector = intel.get("sector_code", "Unknown")
                sector_data = sector_themes.get(company_sector, {})
                signal["sector"] = company_sector
                signal["sector_theme_score"] = sector_data.get("theme_score", 0)
                signal["sector_signal"] = sector_data.get("signal", "neutral")
                signal["sector_confirming"] = (
                    (signal.get("direction") == "BUY" and sector_data.get("theme_score", 0) >= 55)
                    or (signal.get("direction") == "SHORT" and sector_data.get("theme_score", 0) < 45)
                )
                signal["sector_above_threshold"] = sector_data.get("above_threshold", 0)
                validated_signals.append(signal)
        except Exception as e:
            if verbose:
                print(f"  ERROR [{t}]: {e}")

    validated_signals.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)

    buy_signals = [
        s for s in validated_signals if s["direction"] == "BUY" and s["final_signal"] != "AVOID"
    ]
    short_signals = [
        s
        for s in validated_signals
        if s["direction"] == "SHORT" and s["final_signal"] != "AVOID"
    ]
    high_conviction = [
        s for s in validated_signals if "HIGH_CONVICTION" in s.get("final_signal", "")
    ]

    output = {
        "date": date_str,
        "tenant_id": TENANT_ID,
        "regime": regime.get("regime"),
        "total_validated": len(validated_signals),
        "buy_signals": buy_signals,
        "short_signals": short_signals,
        "high_conviction": high_conviction,
        "all_signals": validated_signals,
        "generated_at": datetime.datetime.now().isoformat(),
    }

    os.makedirs(SIGNALS_DIR, exist_ok=True)
    out_file = os.path.join(SIGNALS_DIR, f"validated_signals_{date_str}.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    if save_to_db and not ticker:
        asyncio.run(save_signals_to_db(validated_signals))

    if verbose:
        _print_summary(output)

    return output


def _print_summary(output: dict):
    """Print Layer 3 results summary."""
    print("\n" + "=" * 60)
    print("  LAYER 3 VALIDATED SIGNALS")
    print(f"  Total validated: {output['total_validated']}")
    print(f"  BUY signals:     {len(output['buy_signals'])}")
    print(f"  SHORT signals:   {len(output['short_signals'])}")
    print(f"  High conviction: {len(output['high_conviction'])}")
    print("=" * 60)

    if output.get("buy_signals"):
        print("\n  TOP BUY SETUPS:")
        print(
            f"  {'TICKER':<12} {'CONF':<6} {'SIGNAL':<25} "
            f"{'ENTRY':<10} {'T1':<10} {'SL':<10} R:R"
        )
        print(f"  {'-'*80}")
        for s in output["buy_signals"][:5]:
            print(
                f"  {s['ticker']:<12} "
                f"{s['confidence_score']:<6.0f} "
                f"{s['final_signal']:<25} "
                f"₹{s.get('entry_low', 0):<9.1f} "
                f"₹{s.get('target_1', 0):<9.1f} "
                f"₹{s.get('stop_loss', 0):<9.1f} "
                f"{s.get('risk_reward', 0):.1f}"
            )

    if output.get("short_signals"):
        print("\n  TOP SHORT SETUPS:")
        for s in output["short_signals"][:3]:
            print(
                f"  {s['ticker']:<12} "
                f"Conf:{s['confidence_score']:.0f}  "
                f"Short entry:₹{s.get('entry_high', 0):.1f}  "
                f"T1:₹{s.get('target_1', 0):.1f}  "
                f"SL:₹{s.get('stop_loss', 0):.1f}"
            )
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TradeIQ Layer 3 — Technical Validator")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--ticker", type=str, default=None)
    parser.add_argument("--no-db", action="store_true")
    args = parser.parse_args()
    run_layer3(date_str=args.date, ticker=args.ticker, save_to_db=not args.no_db)

