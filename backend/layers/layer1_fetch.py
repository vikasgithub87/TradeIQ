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

# Short search-friendly names for NewsAPI queries
# Full registered names often return zero results
# These shorter terms match how media actually refers to companies
NEWSAPI_SEARCH_NAMES = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy TCS",
    "HDFCBANK": "HDFC Bank",
    "INFY": "Infosys",
    "ICICIBANK": "ICICI Bank",
    "HINDUNILVR": "Hindustan Unilever HUL",
    "ITC": "ITC Limited cigarettes",
    "SBIN": "State Bank India SBI",
    "BAJFINANCE": "Bajaj Finance",
    "BHARTIARTL": "Airtel Bharti",
    "KOTAKBANK": "Kotak Bank",
    "LT": "Larsen Toubro L&T",
    "AXISBANK": "Axis Bank",
    "ASIANPAINT": "Asian Paints",
    "MARUTI": "Maruti Suzuki",
    "TITAN": "Titan Tata",
    "WIPRO": "Wipro IT",
    "NESTLEIND": "Nestle India",
    "ULTRACEMCO": "UltraTech Cement",
    "POWERGRID": "Power Grid India",
    "NTPC": "NTPC power",
    "ONGC": "ONGC oil",
    "TECHM": "Tech Mahindra",
    "HCLTECH": "HCL Technologies",
    "SUNPHARMA": "Sun Pharma",
    "CIPLA": "Cipla pharma",
    "DRREDDY": "Dr Reddy",
    "BAJAJFINSV": "Bajaj Finserv",
    "ADANIPORTS": "Adani Ports",
    "TMPV": "Tata Motors Passenger Vehicles JLR EV",
    "TMCV": "Tata Motors Commercial Vehicles trucks buses",
    "TATASTEEL": "Tata Steel",
    "JSWSTEEL": "JSW Steel",
    "HINDALCO": "Hindalco",
    "COALINDIA": "Coal India",
    "GRASIM": "Grasim",
    "BRITANNIA": "Britannia biscuits",
    "HEROMOTOCO": "Hero MotoCorp",
    "EICHERMOT": "Eicher Motors Royal Enfield",
    "BPCL": "BPCL Bharat Petroleum",
    "INDUSINDBK": "IndusInd Bank",
    "APOLLOHOSP": "Apollo Hospitals",
    "TATACONSUM": "Tata Consumer",
    "SBILIFE": "SBI Life Insurance",
    "HDFCLIFE": "HDFC Life",
    "BAJAJ-AUTO": "Bajaj Auto",
    "DIVISLAB": "Divi Laboratories",
    "ADANIENT": "Adani Enterprises",
    "TATAPOWER": "Tata Power",
    "M&M": "Mahindra",
    "LTIM": "LTIMindtree",
    "ZOMATO": "Zomato food delivery",
    "DMART": "DMart Avenue Supermarts",
    "IRCTC": "IRCTC railway",
    "HAL": "HAL defence India",
    "BEL": "Bharat Electronics BEL",
    "TVSMOTOR": "TVS Motor",
    "MOTHERSON": "Samvardhana Motherson",
    "BALKRISIND": "Balkrishna Industries BKT tyres",
    "APOLLOTYRE": "Apollo Tyres",
    "ASHOKLEY": "Ashok Leyland",
    "EXIDEIND": "Exide battery",
    "BOSCHLTD": "Bosch India",
    "CEAT": "CEAT tyres",
    "PERSISTENT": "Persistent Systems",
    "COFORGE": "Coforge IT",
    "KPITTECH": "KPIT Technologies",
    "TATAELXSI": "Tata Elxsi",
    "MPHASIS": "Mphasis",
    "DLF": "DLF real estate",
    "GODREJPROP": "Godrej Properties",
    "OBEROIRLTY": "Oberoi Realty",
    "SAIL": "SAIL Steel Authority",
    "NMDC": "NMDC iron ore",
    "HINDZINC": "Hindustan Zinc",
    "VEDL": "Vedanta",
    "RECLTD": "REC Limited power finance",
    "PFC": "Power Finance Corporation",
    "IRFC": "IRFC railway finance",
    "ADANIGREEN": "Adani Green Energy",
    "ADANITRANS": "Adani Transmission",
    "IOC": "Indian Oil Corporation",
    "HINDPETRO": "Hindustan Petroleum HPCL",
    "GAIL": "GAIL gas India",
    "NAUKRI": "Info Edge Naukri",
    "INDIAMART": "IndiaMART",
    "POLICYBZR": "PolicyBazaar PB Fintech",
    "PAYTM": "Paytm One97",
    "NYKAA": "Nykaa beauty",
    "TRENT": "Trent Zudio Westside",
    "JUBLFOOD": "Jubilant FoodWorks Dominos",
    "BANKBARODA": "Bank of Baroda",
    "CANBK": "Canara Bank",
    "PNB": "Punjab National Bank",
    "YESBANK": "Yes Bank",
    "RBLBANK": "RBL Bank",
    "IDFCFIRSTB": "IDFC First Bank",
    "FEDERALBNK": "Federal Bank",
    "BANDHANBNK": "Bandhan Bank",
    "MUTHOOTFIN": "Muthoot Finance gold",
    "CHOLAFIN": "Cholamandalam Finance",
    "MANAPPURAM": "Manappuram Finance",
    "LICHSGFIN": "LIC Housing Finance",
}


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
    "tata motors passenger": "TMPV",
    "tata motors pv": "TMPV",
    "tmpv": "TMPV",
    "tata motors commercial": "TMCV",
    "tata motors cv": "TMCV",
    "tmcv": "TMCV",
    "tata motors": "TMPV",
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


def fetch_google_news_rss(
    ticker: str,
    company_name: str,
    max_articles: int = 5,
) -> list:
    """
    Fetch news from Google News RSS feed.
    Free, unlimited, good coverage of Indian companies.
    Used as fallback when NewsAPI returns zero results.
    """
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET

    # Use short search name if available
    search_name = NEWSAPI_SEARCH_NAMES.get(ticker, company_name)
    # Add India context for better results
    query = f"{search_name} stock India"
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    articles = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        xml = resp.read()
        root = ET.fromstring(xml)

        for item in root.findall(".//item")[:max_articles]:
            title = item.findtext("title", "")
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")
            source_el = item.find("source")
            source = source_el.text if source_el is not None else "Google News"

            if not title or title == "[Removed]":
                continue

            # Parse pubDate to ISO format
            published_at = ""
            try:
                import email.utils

                parsed = email.utils.parsedate_to_datetime(pub_date)
                published_at = parsed.isoformat()
            except Exception:
                published_at = pub_date

            articles.append({
                "headline": title,
                "body": "",
                "source": source,
                "source_trust": get_source_trust(source),
                "published_at": published_at,
                "recency_weight": _compute_recency_weight(published_at),
                "url": link,
                "fingerprint": _headline_fingerprint(title),
            })

    except Exception:
        pass  # Silent fail — return empty list

    return articles


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

    # Use optimised short search name if available
    search_term = NEWSAPI_SEARCH_NAMES.get(ticker, company_name)
    query = f"{search_term} NSE India stock"

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
            rss_articles = fetch_google_news_rss(ticker, company_name, max_articles)
            if rss_articles:
                return rss_articles[:max_articles]
            return _placeholder_articles(ticker)

        raw_articles = data.get("articles", [])
        if not raw_articles:
            # Fallback to Google News RSS
            rss_articles = fetch_google_news_rss(ticker, company_name, max_articles)
            if rss_articles:
                return rss_articles[:max_articles]
            # Final fallback — placeholder
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
        rss_articles = fetch_google_news_rss(ticker, company_name, max_articles)
        if rss_articles:
            return rss_articles[:max_articles]
        return _placeholder_articles(ticker)
    except Exception as e:
        print(f"  WARNING: NewsAPI error for {ticker}: {e}")
        rss_articles = fetch_google_news_rss(ticker, company_name, max_articles)
        if rss_articles:
            return rss_articles[:max_articles]
        return _placeholder_articles(ticker)


def map_entity_to_ticker(text: str) -> list:
    text_lower = text.lower()
    matched = set()
    for name, ticker in COMPANY_NAME_MAP.items():
        if name in text_lower:
            matched.add(ticker)
    return list(matched)

