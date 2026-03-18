"""
layer2_runner.py — TradeIQ Layer 2: BUY Scoring Orchestrator.
"""
import os
import sys
import json
import datetime
import argparse
import asyncio
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.layers.layer2_scoring import (  # noqa: E402
    calculate_buy_score,
    calculate_short_score,
    filter_by_regime,
)
from backend.layers.layer2_themes import calculate_theme_scores, detect_sector_rotation  # noqa: E402
from backend.layers.layer2_velocity import (  # noqa: E402
    load_velocity_history,
    save_velocity_history,
    calculate_velocity,
    update_velocity_history,
)
from backend.layers.layer2_arbitration import arbitrate_direction  # noqa: E402

DATA_DIR = "backend/data"
INTEL_DIR = "backend/data/company_intel"
REGIME_FILE = "backend/data/regime_context.json"
SCORES_DIR = "backend/data/scores"
TENANT_ID = "0001"


def load_regime() -> Dict[str, Any]:
    try:
        if os.path.exists(REGIME_FILE):
            with open(REGIME_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"regime": "RANGE_BOUND", "signal_threshold_l2": 60, "do_not_trade": False}


def load_all_intel(date_str: str) -> List[Dict[str, Any]]:
    if not os.path.exists(INTEL_DIR):
        return []
    out: List[Dict[str, Any]] = []
    for fn in os.listdir(INTEL_DIR):
        if date_str in fn and fn.endswith(".json"):
            try:
                with open(os.path.join(INTEL_DIR, fn)) as f:
                    out.append(json.load(f))
            except Exception:
                continue
    return out


def build_sector_map(intel_list: List[Dict[str, Any]]) -> Dict[str, str]:
    sector_map: Dict[str, str] = {}
    for intel in intel_list:
        tkr = intel.get("ticker", "")
        sector = (
            intel.get("sector_code")
            or intel.get("fundamentals", {}).get("sector")
            or "Unknown"
        )
        if tkr:
            sector_map[tkr] = sector
    return sector_map


async def save_scores_to_db(scores_output: Dict[str, Any]) -> None:
    try:
        from backend.db import AsyncSessionLocal  # type: ignore
        from sqlalchemy import text  # type: ignore

        date_str = scores_output["date"]
        async with AsyncSessionLocal() as session:
            for s in scores_output.get("company_scores", []):
                await session.execute(
                    text(
                        """
                    INSERT INTO trading_scores
                        (id, tenant_id, ticker, date, buy_score,
                         short_score, signal, top_factors)
                    VALUES
                        (gen_random_uuid(), :tenant_id, :ticker, :date,
                         :buy_score, :short_score, :signal, :top_factors)
                    ON CONFLICT (tenant_id, ticker, date)
                    DO UPDATE SET
                        buy_score    = EXCLUDED.buy_score,
                        short_score  = EXCLUDED.short_score,
                        signal       = EXCLUDED.signal,
                        top_factors  = EXCLUDED.top_factors
                """
                    ),
                    {
                        "tenant_id": TENANT_ID,
                        "ticker": s["ticker"],
                        "date": date_str,
                        "buy_score": s["buy_score"],
                        "short_score": s.get("short_score", 0.0),
                        "signal": s["signal"],
                        "top_factors": json.dumps(s.get("top_factors", [])),
                    },
                )
            await session.commit()
            print(f"  Saved {len(scores_output['company_scores'])} scores to database")
    except Exception as e:
        print(f"  WARNING: Could not save to database: {e}")


def run_layer2(
    date_str: Optional[str] = None,
    ticker: Optional[str] = None,
    save_to_db: bool = True,
    verbose: bool = True,
    ignore_regime: bool = False,
    override_threshold: Optional[int] = None,
) -> Dict[str, Any]:
    if not date_str:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    if verbose:
        print("\nTradeIQ Layer 2 — BUY Scoring Engine")
        print(f"Date: {date_str}")
        print("=" * 60)

    regime = load_regime()
    threshold = regime.get("signal_threshold_l2", 60)

    # If caller provides an explicit threshold, honour it (clamped to 0–100)
    if override_threshold is not None:
        try:
            threshold_val = int(override_threshold)
        except (TypeError, ValueError):
            threshold_val = threshold
        threshold = max(0, min(100, threshold_val))

    # When ignore_regime is True and no explicit threshold is given,
    # we still respect the DO_NOT_TRADE label in UI, but use a sane
    # default filter threshold so scores can be inspected.
    if ignore_regime and override_threshold is None:
        threshold = 60
    if regime.get("do_not_trade") and not ignore_regime:
        if verbose:
            print("  DO NOT TRADE day — regime suppresses all signals")
        return {
            "date": date_str,
            "regime": regime.get("regime"),
            "do_not_trade": True,
            "company_scores": [],
            "theme_scores": [],
            "rotation_alerts": [],
            "generated_at": datetime.datetime.now().isoformat(),
        }

    if verbose:
        print(f"  Regime: {regime.get('regime')}  Threshold: ≥{threshold}")

    if ticker:
        fn = f"company_intel_{ticker.upper()}_{date_str}.json"
        fp = os.path.join(INTEL_DIR, fn)
        if not os.path.exists(fp):
            print(f"  ERROR: No intel file for {ticker} on {date_str}")
            return {}
        with open(fp) as f:
            intel_list = [json.load(f)]
    else:
        intel_list = load_all_intel(date_str)

    if verbose:
        print(f"  Loaded {len(intel_list)} company files")
    if not intel_list:
        print("  No intel files found. Run Layer 1 first.")
        return {}

    sector_map = build_sector_map(intel_list)

    prelim_scores = [calculate_buy_score(intel, theme_score=50.0) for intel in intel_list]
    prelim_themes = calculate_theme_scores(prelim_scores, sector_map)
    theme_lookup = {t["sector"]: t["theme_score"] for t in prelim_themes}

    if verbose:
        print(f"  Scoring {len(intel_list)} companies...")

    velocity_history = load_velocity_history()
    company_scores: List[Dict[str, Any]] = []

    for intel in intel_list:
        tkr = intel.get("ticker", "")
        sector = sector_map.get(tkr, "Unknown")
        sector_theme = theme_lookup.get(sector, 50.0)
        score = calculate_buy_score(intel, theme_score=sector_theme)
        short_result = calculate_short_score(intel)
        score["short_score"] = short_result["short_score"]
        score["short_signal"] = short_result["short_signal"]
        score["short_breakdown"] = short_result["short_breakdown"]
        score["short_top_factors"] = short_result["short_top_factors"]
        score["short_flags"] = short_result.get("short_flags", [])
        if "raw_short_score" in short_result:
            score["raw_short_score"] = short_result["raw_short_score"]
        if "short_penalties" in short_result:
            score["short_penalties"] = short_result["short_penalties"]
        if short_result.get("filtered_reason"):
            score["short_filtered_reason"] = short_result["filtered_reason"]
        velocity = calculate_velocity(tkr, score["buy_score"], velocity_history)
        score["velocity"] = velocity
        score["score_delta"] = velocity["delta"]
        score["velocity_label"] = velocity["velocity_label"]
        score["is_breakout"] = velocity["is_breakout"]
        score["streak_days"] = velocity["streak_days"]
        score["sector"] = sector
        velocity_history = update_velocity_history(tkr, score["buy_score"], velocity_history)
        arb_regime = regime.get("regime", "RANGE_BOUND")
        if ignore_regime:
            arb_regime = "RANGE_BOUND"
        score = arbitrate_direction(
            score_result=score,
            intel=intel,
            regime=arb_regime,
            threshold=threshold,
            use_claude=True,
        )
        company_scores.append(score)

    save_velocity_history(velocity_history)
    filtered_scores = filter_by_regime(company_scores, threshold)

    if verbose:
        print(f"  {len(filtered_scores)} companies above threshold {threshold}")

    final_themes = calculate_theme_scores(filtered_scores, sector_map)
    rotation_alerts = detect_sector_rotation(final_themes)

    scores_output: Dict[str, Any] = {
        "date": date_str,
        "tenant_id": TENANT_ID,
        "regime": regime.get("regime"),
        "regime_score": regime.get("regime_score", 50),
        "threshold": threshold,
        "total_companies": len(intel_list),
        "above_threshold": len(filtered_scores),
        "company_scores": filtered_scores,
        "all_scores": sorted(
            company_scores, key=lambda x: x["buy_score"], reverse=True
        ),
        "theme_scores": final_themes,
        "rotation_alerts": rotation_alerts,
        "breakout_stocks": [s for s in filtered_scores if s.get("is_breakout")],
        "generated_at": datetime.datetime.now().isoformat(),
    }

    scores_output["short_scores"] = sorted(
        [
            s
            for s in company_scores
            if s.get("short_score", 0) >= threshold
            and "LOW_LIQUIDITY" not in s.get("short_flags", [])
        ],
        key=lambda x: x["short_score"],
        reverse=True,
    )[:10]

    os.makedirs(SCORES_DIR, exist_ok=True)
    out_file = os.path.join(SCORES_DIR, f"trading_scores_{date_str}.json")
    with open(out_file, "w") as f:
        json.dump(scores_output, f, indent=2)
    if verbose:
        print(f"  Saved: {out_file}")

    if save_to_db and not ticker:
        asyncio.run(save_scores_to_db(scores_output))

    if verbose:
        _print_scores_summary(scores_output)

    return scores_output


def _print_scores_summary(output: Dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("  LAYER 2 SCORES SUMMARY")
    print(f"  Date:    {output['date']}")
    print(f"  Regime:  {output['regime']}")
    print(f"  Scored:  {output['total_companies']} companies")
    print(
        f"  Above threshold ({output['threshold']}): "
        f"{output['above_threshold']}"
    )
    print("=" * 60)
    top_scores = output.get("company_scores", [])[:10]
    if top_scores:
        print("\n  TOP BUY SIGNALS TODAY:")
        print(
            f"  {'TICKER':<14} {'SCORE':<8} {'SIGNAL':<16} "
            f"{'VELOCITY':<14} {'SECTOR'}"
        )
        print(f"  {'-'*70}")
        for s in top_scores:
            vel_label = s.get("velocity_label", "stable")
            breakout = " ⚡" if s.get("is_breakout") else ""
            print(
                f"  {s['ticker']:<14} "
                f"{s['buy_score']:<8.1f} "
                f"{s['signal']:<16} "
                f"{vel_label:<14} "
                f"{s.get('sector', 'Unknown')}{breakout}"
            )
    if output.get("rotation_alerts"):
        print("\n  SECTOR ROTATION ALERTS:")
        for alert in output["rotation_alerts"]:
            print(f"  ⚡ {alert['message']}")
    if output.get("breakout_stocks"):
        tickers = [s["ticker"] for s in output["breakout_stocks"]]
        print("\n  BREAKOUT STOCKS (score surged 15+ points):")
        print(f"  {', '.join(tickers)}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TradeIQ Layer 2 — BUY Scoring Engine"
    )
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--ticker", type=str, default=None)
    parser.add_argument("--no-db", action="store_true")
    args = parser.parse_args()
    run_layer2(date_str=args.date, ticker=args.ticker, save_to_db=not args.no_db)

