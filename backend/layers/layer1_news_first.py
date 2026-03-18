"""
layer1_news_first.py — News-first intelligence pipeline.

Instead of: pick stock → search for its news
This does:  fetch top market news → extract themes → map to stocks

Google News RSS is free, unlimited, and has excellent
Indian financial market coverage. Used as primary source.
NewsAPI is used as supplementary source.
"""
import os
import sys
import json
import time
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.layers.layer1_sources import get_source_trust

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ── Google News RSS Feeds ─────────────────────────────────────────────────────
GOOGLE_NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=NSE+BSE+stock+market+India&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=Nifty+Sensex+India+market&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=India+stock+earnings+results&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=RBI+SEBI+India+finance&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=crude+oil+dollar+rupee+India&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=India+IT+technology+sector&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=India+banking+HDFC+ICICI+SBI&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=India+pharma+drug+approval&hl=en-IN&gl=IN&ceid=IN:en",
]

# ── NSE Sector and Ticker Mapping ─────────────────────────────────────────────
THEME_TICKER_MAP = {
    "rbi rate": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BAJFINANCE", "RECLTD", "PFC"],
    "rbi policy": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BAJFINANCE"],
    "repo rate": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "BAJFINANCE", "LICHSGFIN"],
    "inflation": ["HINDUNILVR", "ITC", "BRITANNIA", "NESTLEIND", "MARUTI", "HEROMOTOCO"],
    "gdp growth": ["RELIANCE", "TCS", "HDFCBANK", "LT", "MARUTI", "SBIN"],
    "budget": ["LT", "NTPC", "POWERGRID", "HAL", "BEL", "IRCTC", "COALINDIA"],
    "fiscal deficit": ["SBIN", "LT", "NTPC", "POWERGRID", "RECLTD", "PFC"],
    "crude oil": ["ONGC", "BPCL", "IOC", "HINDPETRO", "RELIANCE", "GAIL", "PETRONET"],
    "oil prices": ["ONGC", "BPCL", "IOC", "HINDPETRO", "RELIANCE", "M&M"],
    "gold price": ["TITAN", "MUTHOOTFIN", "MANAPPURAM"],
    "steel prices": ["TATASTEEL", "JSWSTEEL", "SAIL", "HINDALCO", "NMDC"],
    "aluminium": ["HINDALCO", "NALCO", "VEDL"],
    "coal": ["COALINDIA", "NTPC", "TATAPOWER"],
    "rupee dollar": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "ONGC", "BPCL"],
    "dollar strengthens": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "MPHASIS"],
    "rupee weakens": ["TCS", "INFY", "WIPRO", "HCLTECH", "ONGC", "BPCL", "IOC"],
    "it sector": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "PERSISTENT"],
    "banking sector": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK"],
    "pharma sector": ["SUNPHARMA", "CIPLA", "DRREDDY", "DIVISLAB", "LUPIN", "AUROPHARMA"],
    "auto sector": ["TMPV", "TMCV", "MARUTI", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT"],
    "fmcg sector": ["HINDUNILVR", "ITC", "BRITANNIA", "NESTLEIND", "DABUR", "MARICO"],
    "infra sector": ["LT", "ULTRACEMCO", "NTPC", "POWERGRID", "ADANIPORTS", "HAL", "BEL"],
    "real estate": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE"],
    "metal sector": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "SAIL", "NMDC", "VEDL"],
    "energy sector": ["RELIANCE", "ONGC", "BPCL", "TATAPOWER", "ADANIGREEN", "NTPC"],
    "telecom sector": ["BHARTIARTL", "IDEA", "TATACOMM"],
    "fii buying": ["HDFCBANK", "ICICIBANK", "RELIANCE", "TCS", "INFY", "SBIN"],
    "fii selling": ["HDFCBANK", "ICICIBANK", "RELIANCE", "TCS", "INFY"],
    "sebi": ["NAUKRI", "ZOMATO", "PAYTM", "NYKAA"],
    "ipo": ["ZOMATO", "NYKAA", "PAYTM", "POLICYBZR", "DMART"],
    "us recession": ["TCS", "INFY", "WIPRO", "HCLTECH", "ONGC", "RELIANCE"],
    "china economy": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "NMDC", "VEDL"],
    "war conflict": ["HAL", "BEL", "ONGC", "BPCL", "RELIANCE", "TATASTEEL", "NMDC"],
    "middle east": ["ONGC", "BPCL", "IOC", "HINDPETRO", "RELIANCE", "HAL", "BEL"],
    "ai artificial intelligence": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "PERSISTENT"],
    "electric vehicle": ["TMPV", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "TATAPOWER", "EXIDEIND"],
    "climate renewable": ["TATAPOWER", "ADANIGREEN", "NTPC", "POWERGRID"],
    "jio": ["RELIANCE"],
    "tata": ["TATASTEEL", "TMPV", "TMCV", "TCS", "TATAPOWER", "TATACONSUM"],
    "adani": ["ADANIENT", "ADANIPORTS", "ADANIGREEN"],
    "infosys": ["INFY"],
    "wipro": ["WIPRO"],
    "hdfc": ["HDFCBANK", "HDFCLIFE"],
    "icici": ["ICICIBANK"],
    "bajaj": ["BAJFINANCE", "BAJAJFINSV", "BAJAJ-AUTO"],
    "mahindra": ["M&M"],
    "maruti suzuki": ["MARUTI"],
    "asian paints": ["ASIANPAINT"],
    "sun pharma": ["SUNPHARMA"],
}


def fetch_google_news_headlines(max_per_feed: int = 10, max_total: int = 60) -> list:
    """
    Fetch top Indian market headlines from multiple Google News RSS feeds.
    Returns deduplicated list sorted by recency.
    """
    all_articles = []
    seen_titles = set()

    for feed_url in GOOGLE_NEWS_FEEDS:
        try:
            req = urllib.request.Request(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            resp = urllib.request.urlopen(req, timeout=10)
            root = ET.fromstring(resp.read())

            for item in root.findall(".//item")[:max_per_feed]:
                title = (item.findtext("title") or "").strip()
                pub_date = item.findtext("pubDate") or ""
                link = item.findtext("link") or ""
                source_el = item.find("source")
                source = source_el.text if source_el is not None else "Google News"

                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                published_at = pub_date
                try:
                    import email.utils

                    parsed = email.utils.parsedate_to_datetime(pub_date)
                    published_at = parsed.isoformat()
                except Exception:
                    pass

                all_articles.append(
                    {
                        "headline": title,
                        "source": source,
                        "source_trust": get_source_trust(source),
                        "published_at": published_at,
                        "url": link,
                        "body": "",
                    }
                )

            time.sleep(0.3)
        except Exception:
            continue

    all_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return all_articles[:max_total]


def extract_themes_rule_based(headlines: list) -> dict:
    """
    Fast rule-based theme extraction — maps headlines to affected tickers
    using THEME_TICKER_MAP keywords.
    Returns: {ticker: [list of relevant headlines]}
    """
    ticker_headlines: dict = {}

    for article in headlines:
        text = (article.get("headline") or "").lower()
        for keyword, tickers in THEME_TICKER_MAP.items():
            if keyword in text:
                for ticker in tickers:
                    ticker_headlines.setdefault(ticker, [])
                    ticker_headlines[ticker].append(article)

    return ticker_headlines


def extract_themes_claude(headlines: list) -> dict:
    """
    Claude-powered theme extraction — falls back to rule-based on error.
    """
    if not ANTHROPIC_API_KEY or not headlines:
        return extract_themes_rule_based(headlines)

    import requests

    headline_text = "\n".join(
        [f"{i+1}. {a['headline']} [{a.get('source','')}]"
         for i, a in enumerate(headlines[:30])]
    )

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
                "max_tokens": 1500,
                "system": (
                    "You are a senior NSE India equity analyst. "
                    "Analyse news headlines and identify which NSE-listed "
                    "companies will be most impacted today. "
                    "Return ONLY valid JSON — no other text."
                ),
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Today's top Indian market headlines:
{headline_text}

Identify the 10-15 NSE-listed companies most likely to have significant
intraday price movement based on these headlines.

Return this exact JSON format:
{{
  "themes": ["list of 3-5 key market themes today"],
  "impacted_companies": [
    {{
      "ticker": "NSE_TICKER",
      "impact_direction": "positive|negative|mixed",
      "impact_strength": "HIGH|MEDIUM|LOW",
      "driving_headlines": ["headline 1", "headline 2"],
      "reason": "one sentence why this company is impacted"
    }}
  ],
  "market_sentiment": "bullish|bearish|mixed",
  "key_risk": "single biggest risk for intraday traders today"
}}""",
                    }
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        ticker_map: dict = {}
        for company in data.get("impacted_companies", []):
            ticker = (company.get("ticker") or "").upper().strip()
            if not ticker:
                continue
            ticker_map[ticker] = {
                "headlines": company.get("driving_headlines", []),
                "impact_direction": company.get("impact_direction", "mixed"),
                "impact_strength": company.get("impact_strength", "MEDIUM"),
                "reason": company.get("reason", ""),
            }

        return {
            "_themes": data.get("themes", []),
            "_market_sentiment": data.get("market_sentiment", "mixed"),
            "_key_risk": data.get("key_risk", ""),
            "_method": "claude",
            **ticker_map,
        }
    except Exception as e:
        print(f"  WARNING: Claude theme extraction failed: {e}")
        return {**extract_themes_rule_based(headlines), "_method": "rule_based"}


def build_impacted_company_list(ticker_map: dict, max_count: int = 30) -> list:
    """Convert ticker→headlines map into a company list for Smart Scan."""
    from backend.layers.layer1_news import DEFAULT_WATCHLIST

    watchlist_map = {c["ticker"]: c for c in DEFAULT_WATCHLIST}
    companies = []
    seen = set()

    for ticker, data in ticker_map.items():
        if str(ticker).startswith("_") or ticker in seen:
            continue

        wl_entry = watchlist_map.get(ticker, {})
        reason = data.get("reason", "") if isinstance(data, dict) else ""
        strength = data.get("impact_strength", "MEDIUM") if isinstance(data, dict) else "MEDIUM"

        companies.append(
            {
                "ticker": ticker,
                "name": wl_entry.get("name", ticker),
                "sector": wl_entry.get("sector", "Unknown"),
                "reason": reason,
                "strength": strength,
            }
        )
        seen.add(ticker)

    strength_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    companies.sort(key=lambda x: strength_order.get(x.get("strength", "MEDIUM"), 1))
    return companies[:max_count]


def run_news_first_scan(
    max_companies: int = 30,
    use_claude: bool = True,
    save_result: bool = True,
) -> dict:
    """
    Full news-first pipeline:
    1. Fetch top Indian market headlines from Google News
    2. Extract themes and map to affected stocks
    3. Return structured result for Smart Scan or UI
    """
    print("\nTradeIQ News-First Scanner")
    print("=" * 50)

    print("  Fetching Google News headlines...")
    headlines = fetch_google_news_headlines()
    print(f"  Fetched {len(headlines)} unique headlines")

    if not headlines:
        print("  WARNING: No headlines fetched — check internet connection")
        return {"headlines": [], "companies": [], "themes": [], "error": "no_headlines"}

    if use_claude and ANTHROPIC_API_KEY:
        print("  Extracting themes with Claude AI...")
        ticker_map = extract_themes_claude(headlines)
    else:
        print("  Extracting themes (rule-based)...")
        ticker_map = extract_themes_rule_based(headlines)

    method = ticker_map.get("_method", "rule_based") if isinstance(ticker_map, dict) else "rule_based"
    themes = ticker_map.get("_themes", []) if isinstance(ticker_map, dict) else []
    sentiment = ticker_map.get("_market_sentiment", "mixed") if isinstance(ticker_map, dict) else "mixed"
    key_risk = ticker_map.get("_key_risk", "") if isinstance(ticker_map, dict) else ""

    print(f"  Extraction method: {method}")
    print(f"  Themes identified: {len(themes)}")

    companies = build_impacted_company_list(ticker_map, max_companies) if isinstance(ticker_map, dict) else []
    print(f"  Companies identified: {len(companies)}")

    result = {
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "generated_at": datetime.datetime.now().isoformat(),
        "method": method,
        "headline_count": len(headlines),
        "headlines": headlines[:20],
        "themes": themes,
        "market_sentiment": sentiment,
        "key_risk": key_risk,
        "companies": companies,
        "ticker_count": len(companies),
    }

    if save_result:
        os.makedirs("backend/data", exist_ok=True)
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        out_file = f"backend/data/news_first_{date_str}.json"
        with open(out_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Saved: {out_file}")

    print("\n  Top headlines driving markets today:")
    for h in headlines[:5]:
        print(f"    - {h.get('headline','')[:80]}")
    if themes:
        print(f"\n  Key themes: {', '.join(themes[:4])}")
    print(f"\n  Companies impacted ({len(companies)}):")
    for c in companies[:10]:
        print(f"    {c['ticker']:<14} [{c.get('strength','?')}] {str(c.get('reason',''))[:50]}")
    print("=" * 50)

    return result


if __name__ == "__main__":
    use_claude = "--no-claude" not in sys.argv
    result = run_news_first_scan(use_claude=use_claude)
    print(f"\nResult saved. {result.get('ticker_count', 0)} companies identified.")

