"""
layer2_arbitration.py — Direction conflict resolution for Layer 2.

When a company scores above threshold on BOTH buy_score and
short_score simultaneously, this module resolves the conflict
by calling Claude API (Prompt 2 from the TradeIQ spec) and
returns a single recommended direction with reasoning.

Also applies regime-based short suppression rules:
- TRENDING_BULL regime: shorts require short_score >= 82
- EXPIRY_CAUTION: both directions require higher confidence
- DO_NOT_TRADE: all signals suppressed (handled in runner)
"""
import json
import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

REGIME_SHORT_RULES = {
    "TRENDING_BULL": {"min_short_score": 82, "suppress": False},
    "TRENDING_BEAR": {"min_short_score": 50, "suppress": False},
    "RANGE_BOUND": {"min_short_score": 65, "suppress": False},
    "HIGH_VOLATILITY": {"min_short_score": 75, "suppress": False},
    "EXPIRY_CAUTION": {"min_short_score": 78, "suppress": False},
    "DO_NOT_TRADE": {"min_short_score": 999, "suppress": True},
    "MARKET_CLOSED": {"min_short_score": 999, "suppress": True},
}

REGIME_BUY_RULES = {
    "TRENDING_BULL": {"min_buy_score": 60, "suppress": False},
    "TRENDING_BEAR": {"min_buy_score": 75, "suppress": False},
    "RANGE_BOUND": {"min_buy_score": 72, "suppress": False},
    "HIGH_VOLATILITY": {"min_buy_score": 78, "suppress": False},
    "EXPIRY_CAUTION": {"min_buy_score": 80, "suppress": False},
    "DO_NOT_TRADE": {"min_buy_score": 999, "suppress": True},
    "MARKET_CLOSED": {"min_buy_score": 999, "suppress": True},
}


def apply_regime_suppression(score_result: dict, regime: str) -> dict:
    if "flags" not in score_result:
        score_result["flags"] = []

    short_rules = REGIME_SHORT_RULES.get(
        regime, {"min_short_score": 65, "suppress": False}
    )
    short_score = score_result.get("short_score", 0)

    if short_rules["suppress"]:
        score_result["short_score"] = 0.0
        score_result["short_signal"] = "no_short"
        score_result["regime_suppressed_short"] = True
        if "REGIME_SUPPRESSED_SHORT" not in score_result["flags"]:
            score_result["flags"].append("REGIME_SUPPRESSED_SHORT")
    elif short_score < short_rules["min_short_score"]:
        score_result["regime_suppressed_short"] = True
        score_result["short_score"] = 0.0
        score_result["short_signal"] = "no_short"
        if "REGIME_SUPPRESSED_SHORT" not in score_result["flags"]:
            score_result["flags"].append("REGIME_SUPPRESSED_SHORT")
        if regime == "TRENDING_BULL":
            score_result["flags"].append("TRENDING_BULL_SHORT_SUPPRESSED")
    else:
        score_result["regime_suppressed_short"] = False

    buy_rules = REGIME_BUY_RULES.get(
        regime, {"min_buy_score": 60, "suppress": False}
    )
    buy_score = score_result.get("buy_score", 0)

    if buy_rules["suppress"]:
        score_result["buy_score"] = 0.0
        score_result["signal"] = "avoid"
        score_result["regime_suppressed_buy"] = True
        if "REGIME_SUPPRESSED_BUY" not in score_result["flags"]:
            score_result["flags"].append("REGIME_SUPPRESSED_BUY")
    elif buy_score < buy_rules["min_buy_score"]:
        score_result["regime_suppressed_buy"] = True
    else:
        score_result["regime_suppressed_buy"] = False

    return score_result


def is_direction_conflict(
    buy_score: float,
    short_score: float,
    threshold: int = 60,
) -> bool:
    return buy_score >= threshold and short_score >= threshold


def resolve_conflict_rule_based(score_result: dict, regime: str) -> dict:
    buy_score = score_result.get("buy_score", 0)
    short_score = score_result.get("short_score", 0)

    if score_result.get("regime_suppressed_short"):
        direction = "LONG"
        reason = f"Short suppressed by {regime} regime rules"
    elif score_result.get("regime_suppressed_buy"):
        direction = "SHORT"
        reason = f"Buy suppressed by {regime} regime rules"
    elif regime == "TRENDING_BULL" and buy_score > 0:
        direction = "LONG"
        reason = "TRENDING_BULL regime favours long side"
    elif regime == "TRENDING_BEAR" and short_score > 0:
        direction = "SHORT"
        reason = "TRENDING_BEAR regime favours short side"
    elif buy_score - short_score >= 10:
        direction = "LONG"
        reason = (
            f"BUY score {buy_score:.0f} leads SHORT {short_score:.0f} by margin"
        )
    elif short_score - buy_score >= 10:
        direction = "SHORT"
        reason = (
            f"SHORT score {short_score:.0f} leads BUY {buy_score:.0f} by margin"
        )
    elif buy_score > 0 and short_score > 0:
        if buy_score == short_score:
            direction = "NEUTRAL"
            reason = (
                f"Scores tied ({buy_score:.0f}) — conflicting signals"
            )
        elif buy_score > short_score:
            direction = "LONG"
            reason = (
                f"BUY {buy_score:.0f} edges SHORT {short_score:.0f} (marginal)"
            )
        else:
            direction = "SHORT"
            reason = (
                f"SHORT {short_score:.0f} edges BUY {buy_score:.0f} (marginal)"
            )
    else:
        direction = "LONG" if buy_score > short_score else "SHORT"
        reason = "Default direction by higher score"

    score_result["recommended_direction"] = direction
    score_result["direction_reason"] = reason
    score_result["arbitration_method"] = "rule_based"
    score_result["direction_conflict"] = True

    return score_result


def resolve_conflict_claude(
    score_result: dict,
    intel: dict,
    regime: str,
) -> dict:
    if not ANTHROPIC_API_KEY:
        return resolve_conflict_rule_based(score_result, regime)

    ticker = score_result.get("ticker", "")
    buy_score = score_result.get("buy_score", 0)
    short_score = score_result.get("short_score", 0)

    buy_factors = json.dumps(score_result.get("score_breakdown", {}))
    short_factors = json.dumps(score_result.get("short_breakdown", {}))

    user_prompt = f"""Stock: {ticker} | Regime: {regime}
Long score raw: {buy_score}/100 | Short score raw: {short_score}/100

Long factor breakdown: {buy_factors}
Short factor breakdown: {short_factors}

Catalyst summary: {intel.get('catalyst_summary', 'No summary available')}
Dominant direction from news: {intel.get('dominant_direction', 'NEUTRAL')}
FII activity: {intel.get('fii_activity', 'neutral')}
PCR: {intel.get('pcr', 1.0)}
OI signal: {intel.get('oi_signal', 'neutral')}
Near 52W high: {intel.get('near_52w_high', False)}

Return ONLY this JSON:
{{
  "recommended_direction": "LONG|SHORT|NEUTRAL",
  "direction_rationale": "one sentence explanation for a trader",
  "buy_score_validated": {buy_score},
  "short_score_validated": {short_score},
  "key_risks": ["risk1", "risk2"],
  "pass_to_l3": true
}}"""

    try:
        resp = requests.post(
            CLAUDE_API_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 400,
                "system": (
                    "You are a quantitative trading strategist for NSE India "
                    "intraday markets. A company has both strong buy and short "
                    "signals simultaneously. Resolve the conflict and recommend "
                    "ONE direction. Return only valid JSON."
                ),
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["content"][0]["text"].strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)

        score_result["recommended_direction"] = result.get(
            "recommended_direction", "NEUTRAL"
        )
        score_result["direction_reason"] = result.get(
            "direction_rationale", "Claude arbitration"
        )
        score_result["key_risks"] = result.get("key_risks", [])
        score_result["arbitration_method"] = "claude_api"
        score_result["direction_conflict"] = True

        return score_result

    except Exception as e:
        print(f"  WARNING: Claude arbitration failed for {ticker}: {e}")
        return resolve_conflict_rule_based(score_result, regime)


def arbitrate_direction(
    score_result: dict,
    intel: dict,
    regime: str,
    threshold: int = 60,
    use_claude: bool = True,
) -> dict:
    score_result = apply_regime_suppression(score_result, regime)

    buy_score = score_result.get("buy_score", 0)
    short_score = score_result.get("short_score", 0)

    conflict = is_direction_conflict(buy_score, short_score, threshold)

    if conflict:
        if use_claude:
            score_result = resolve_conflict_claude(score_result, intel, regime)
        else:
            score_result = resolve_conflict_rule_based(score_result, regime)
    else:
        score_result["direction_conflict"] = False
        score_result["arbitration_method"] = "no_conflict"

        if buy_score >= threshold and short_score < threshold:
            score_result["recommended_direction"] = "LONG"
            score_result["direction_reason"] = (
                f"Clear long signal: score {buy_score:.0f}"
            )
        elif short_score >= threshold and buy_score < threshold:
            score_result["recommended_direction"] = "SHORT"
            score_result["direction_reason"] = (
                f"Clear short signal: score {short_score:.0f}"
            )
        else:
            score_result["recommended_direction"] = "NEUTRAL"
            score_result["direction_reason"] = "No signal above threshold"

    flags = list(score_result.get("flags", []))

    if short_score >= 75 and (intel.get("pcr") or 1.0) >= 0.8:
        flags.append("SHORT_REQUIRES_PCR_CONFIRM")

    if conflict:
        flags.append("DIRECTION_CONFLICT_RESOLVED")

    if (
        score_result.get("recommended_direction") == "SHORT"
        and intel.get("near_52w_high")
    ):
        flags.append("SHORT_EXHAUSTION_SETUP")

    if intel.get("results_expected"):
        flags.append("RESULTS_GAP_RISK")

    score_result["flags"] = list(set(flags))
    score_result["l3_flags"] = score_result["flags"]
    score_result["ready_for_l3"] = (
        score_result.get("recommended_direction") != "NEUTRAL"
        and (buy_score >= threshold or short_score >= threshold)
    )

    return score_result
