"""
layer1_fetch.py — NewsAPI fetcher with smart deduplication.
"""
import os
import hashlib
import datetime
from typing import Optional, List, Dict

import requests
from dotenv import load_dotenv

from backend.layers.layer1_sources import get_source_trust

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_BASE = "https://newsapi.org/v2/everything"


COMPANY_NAME_MAP = {
    "reliance industries": "RELIANCE",
    "reliance": "RELIANCE",
    "jio": "RELIANCE",
    "tata consultancy": "TCS",
    "tcs": "TCS",
    "hdfc bank": "HDFCBANK",
    "hdfc": "HDFCBANK",
    "infosys": "INFY",
    "icici bank": "ICICIBANK",
    "icici": "ICICIBANK",
    "hindustan unilever": "HINDUNILVR",
    "hul": "HINDUNILVR",
    "itc": "ITC",
    "state bank": "SBIN",
    "sbi": "SBIN",
    "bajaj finance": "BAJFINANCE",
    "bharti airtel": "BHARTIARTL",
    "airtel": "BHARTIARTL",
    "kotak mahindra": "KOTAKBANK",
    "kotak": "KOTAKBANK",
    "larsen": "LT",
    "l&t": "LT",
    "asian paints": "ASIANPAINT",
    "axis bank": "AXISBANK",
    "maruti suzuki": "MARUTI",
    "maruti": "MARUTI",
    "titan": "TITAN",
    "wipro": "WIPRO",
    "nestle": "NESTLEIND",
    "ultratech": "ULTRACEMCO",
    "ntpc": "NTPC",
    "ongc": "ONGC",
    "tech mahindra": "TECHM",
    "hcl tech": "HCLTECH",
    "hcl technologies": "HCLTECH",
    "sun pharma": "SUNPHARMA",
    "sun pharmaceutical": "SUNPHARMA",
    "cipla": "CIPLA",
    "dr reddy": "DRREDDY",
    "tata motors": "TATAMOTORS",
    "tata steel": "TATASTEEL",
    "jsw steel": "JSWSTEEL",
    "hindalco": "HINDALCO",
    "coal india": "COALINDIA",
    "hero motocorp": "HEROMOTOCO",
    "hero moto": "HEROMOTOCO",
    "bajaj auto": "BAJAJ-AUTO",
    "bpcl": "BPCL",
    "bharat petroleum": "BPCL",
    "indusind bank": "INDUSINDBK",
    "mahindra": "M&M",
    "adani": "ADANIENT",
    "apollo hospitals": "APOLLOHOSP",
    "zomato": "ZOMATO",
    "dmart": "DMART",
    "avenue supermarts": "DMART",
    "trent": "TRENT",
    "nykaa": "NYKAA",
    "paytm": "PAYTM",
    "irctc": "IRCTC",
    "hal": "HAL",
    "hindustan aeronautics": "HAL",
    "bel": "BEL",
    "bharat electronics": "BEL",
    "dlf": "DLF",
    "godrej properties": "GODREJPROP",
    "ltimindtree": "LTIM",
    "mphasis": "MPHASIS",
    "persistent": "PERSISTENT",
}


def _headline_fingerprint(headline: str) -> str:
    normalised = " ".join(headline.lower().split())[:60]
    return hashlib.md5(normalised.encode()).hexdigest()[:12]


def _compute_recency_weight(published_at: str) -> float:
    try:
        pub_time = datetime.datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )
        now = datetime.datetime.now(datetime.timezone.utc)
        age_hrs = (now - pub_time).total_seconds() / 3600
        if age_hrs < 2:
            return 3.0
        if age_hrs < 6:
            return 2.0
        if age_hrs < 12:
            return 1.5
        if age_hrs < 24:
            return 1.0
        return 0.5
    except Exception:
        return 1.0


def _placeholder_articles(ticker: str) -> List[Dict]:
    return [{
        "headline": f"No recent news found for {ticker}",
        "body": "",
        "source": "none",
        "source_trust": 0.0,
        "published_at": "",
        "recency_weight": 0.0,
        "url": "",
        "fingerprint": "placeholder",
    }]


def fetch_news(
    ticker: str,
    company_name: str,
    max_articles: int = 10,
    days_back: int = 2,
) -> List[Dict]:
    if not NEWSAPI_KEY:
        print(f"  WARNING: NEWSAPI_KEY not set — returning placeholder for {ticker}")
        return _placeholder_articles(ticker)

    from_date = (
        datetime.date.today() - datetime.timedelta(days=days_back)
    ).strftime("%Y-%m-%d")

    query = f'"{company_name}" India NSE'

    try:
        resp = requests.get(
            NEWSAPI_BASE,
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(max_articles * 2, 50),
                "from": from_date,
                "apiKey": NEWSAPI_KEY,
            },
            timeout=12,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            print(f"  WARNING: NewsAPI error for {ticker}: {data.get('message')}")
            return _placeholder_articles(ticker)

        raw_articles = data.get("articles", [])
        if not raw_articles:
            print(f"  WARNING: No articles found for {ticker}")
            return _placeholder_articles(ticker)

        seen_fps = set()
        articles: List[Dict] = []

        for art in raw_articles:
            headline = (art.get("title") or "").strip()
            if not headline or headline == "[Removed]":
                continue
            fp = _headline_fingerprint(headline)
            if fp in seen_fps:
                continue
            seen_fps.add(fp)

            source_name = (art.get("source") or {}).get("name", "Unknown")
            source_trust = get_source_trust(source_name)
            published_at = art.get("publishedAt", "")
            recency_weight = _compute_recency_weight(published_at)

            articles.append({
                "headline": headline,
                "body": (art.get("description") or "")[:500],
                "source": source_name,
                "source_trust": source_trust,
                "published_at": published_at,
                "recency_weight": recency_weight,
                "url": art.get("url", ""),
                "fingerprint": fp,
            })

        articles.sort(
            key=lambda a: a["recency_weight"] * a["source_trust"],
            reverse=True,
        )
        return articles[:max_articles]

    except requests.exceptions.Timeout:
        print(f"  WARNING: NewsAPI timeout for {ticker}")
        return _placeholder_articles(ticker)
    except Exception as e:
        print(f"  WARNING: NewsAPI error for {ticker}: {e}")
        return _placeholder_articles(ticker)


def map_entity_to_ticker(text: str) -> list:
    text_lower = text.lower()
    matched = set()
    for name, ticker in COMPANY_NAME_MAP.items():
        if name in text_lower:
            matched.add(ticker)
    return list(matched)

