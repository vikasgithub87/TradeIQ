"""
layer1_sentiment.py — Claude API sentiment and catalyst analysis.
"""
import os
import json
from typing import Optional, List, Dict

import requests
from dotenv import load_dotenv

from backend.layers.layer1_sources import get_source_trust, get_catalyst_info

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

SYSTEM_PROMPT = (
    "You are a senior equity analyst covering NSE-listed companies for intraday traders. "
    "You analyse news articles, identify LONG and SHORT catalysts, and output only JSON."
)


def _empty_sentiment(ticker: str) -> Dict:
    return {
        "ticker": ticker,
        "long_catalysts": [],
        "short_catalysts": [],
        "net_sentiment_score": 0.0,
        "dominant_direction": "NEUTRAL",
        "intraday_relevance": "LOW",
        "catalyst_summary": f"No significant news found for {ticker} today.",
    }


def _fallback_sentiment(ticker: str, articles: List[Dict]) -> Dict:
    positive_keywords = [
        "profit", "growth", "beats", "record", "launches",
        "wins", "rises", "surge", "strong", "positive",
        "upgrade", "buy", "outperform", "dividend", "expansion",
    ]
    negative_keywords = [
        "loss", "miss", "decline", "falls", "fraud",
        "probe", "penalty", "warning", "weak", "cut",
        "downgrade", "sell", "underperform", "debt", "concern",
    ]

    pos_score = 0.0
    neg_score = 0.0
    for art in articles:
        text = (art.get("headline", "") + " " + art.get("body", "")).lower()
        trust = art.get("source_trust", 0.5)
        rec = art.get("recency_weight", 1.0)
        weight = trust * min(rec, 2.0)
        pos = sum(1 for k in positive_keywords if k in text)
        neg = sum(1 for k in negative_keywords if k in text)
        pos_score += pos * weight
        neg_score += neg * weight

    total = pos_score + neg_score
    if total == 0:
        net = 0.0
    else:
        net = round((pos_score - neg_score) / total, 3)

    direction = "LONG" if net > 0.15 else "SHORT" if net < -0.15 else "NEUTRAL"

    return {
        "ticker": ticker,
        "long_catalysts": [],
        "short_catalysts": [],
        "net_sentiment_score": net,
        "dominant_direction": direction,
        "intraday_relevance": "MEDIUM" if total > 0 else "LOW",
        "catalyst_summary": f"Fallback analysis for {ticker}: {direction} bias.",
    }


def _apply_weights(result: Dict, articles: List[Dict]) -> Dict:
    lookup = {}
    for a in articles:
        lookup[a.get("source", "").lower()] = (
            a.get("source_trust", 0.6),
            a.get("recency_weight", 1.0),
        )

    def adjust(cats: List[Dict]) -> List[Dict]:
        for c in cats:
            source = c.get("source", "").lower()
            trust, rec = lookup.get(source, (0.6, 1.0))
            base = c.get("intensity", 0.5)
            adjusted = base * (0.6 + 0.4 * trust) * min(rec / 2.0, 1.5)
            c["intensity"] = round(min(adjusted, 1.0), 3)
            c["source_trust"] = trust
            c["recency_weight"] = rec
        return cats

    result["long_catalysts"] = adjust(result.get("long_catalysts", []))
    result["short_catalysts"] = adjust(result.get("short_catalysts", []))
    return result


def analyse_sentiment(
    ticker: str,
    company_name: str,
    articles: List[Dict],
    regime_context: Optional[Dict] = None,
) -> Dict:
    if not articles or articles[0].get("fingerprint") == "placeholder":
        return _empty_sentiment(ticker)
    if not ANTHROPIC_API_KEY:
        return _fallback_sentiment(ticker, articles)

    lines = []
    for i, art in enumerate(articles[:8], 1):
        trust_label = (
            "HIGH-TRUST" if art["source_trust"] >= 0.80
            else "MEDIUM-TRUST" if art["source_trust"] >= 0.60
            else "LOW-TRUST"
        )
        rec_label = (
            "BREAKING" if art["recency_weight"] >= 3.0
            else "RECENT" if art["recency_weight"] >= 2.0
            else "TODAY" if art["recency_weight"] >= 1.0
            else "OLDER"
        )
        lines.append(
            f"{i}. [{rec_label}][{trust_label}] {art['source']}: "
            f"{art['headline']}. {art.get('body','')}"
        )
    articles_text = "\n".join(lines)

    regime_note = ""
    if regime_context:
        regime_note = (
            f"\nMarket regime today: {regime_context.get('regime', 'UNKNOWN')}. "
            f"India VIX: {regime_context.get('india_vix', 'N/A')}."
        )

    user_prompt = f"""Analyse these news articles for {company_name} ({ticker}) listed on NSE India.{regime_note}

Articles (newest first, with source trust and recency labels):
{articles_text}

Return ONLY this JSON structure — no other text:
{{
  "long_catalysts": [
    {{
      "type": "earnings_beat|product_launch|contract_win|fii_buying|promoter_buying|guidance_raised|dividend_declared|buyback_announced|capacity_expansion|sector_tailwind|analyst_coverage|other",
      "headline": "copy the exact headline",
      "source": "source name",
      "intensity": 0.0-1.0,
      "key_fact": "the single most important specific fact (use numbers if available)",
      "intraday_relevance": "HIGH|MEDIUM|LOW"
    }}
  ],
  "short_catalysts": [
    {{
      "type": "earnings_miss|guidance_cut|regulatory_action|sebi_notice|ed_raid|management_exit|promoter_pledge|fii_selling|debt_concern|litigation_risk|sector_headwind|other",
      "headline": "copy the exact headline",
      "source": "source name",
      "intensity": 0.0-1.0,
      "key_fact": "the single most important specific fact",
      "intraday_relevance": "HIGH|MEDIUM|LOW"
    }}
  ],
  "net_sentiment_score": -1.0 to 1.0,
  "dominant_direction": "LONG|SHORT|NEUTRAL",
  "intraday_relevance": "HIGH|MEDIUM|LOW",
  "catalyst_summary": "one sentence — the single most actionable insight for an intraday trader today"
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
                "max_tokens": 1200,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["content"][0]["text"].strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) > 1:
                raw = parts[1]
                if raw.startswith("json"):
                    raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
        result = _apply_weights(result, articles)
        result["ticker"] = ticker
        return result
    except Exception as e:
        print(f"  WARNING: Claude API error for {ticker}: {e}")
        return _fallback_sentiment(ticker, articles)

