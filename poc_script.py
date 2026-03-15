import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
if not ANTHROPIC_API_KEY or not NEWSAPI_KEY:
    print("ERROR: Missing API keys. Set ANTHROPIC_API_KEY and NEWSAPI_KEY in .env")
    sys.exit(1)

TICKER = "RELIANCE"  # Default company ticker (script runs 3 companies in main)

def fetch_news(company_name: str, ticker: str) -> list:
    """Fetch 5 most recent English news articles for the company from NewsAPI."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": f"{company_name} India NSE stock",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWSAPI_KEY,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles") or []
        if not articles:
            raise ValueError("No articles")
        return [{"headline": a["title"], "body": a.get("description") or "", "source": a.get("source", {}).get("name", ""), "published_at": a.get("publishedAt", "")} for a in articles]
    except Exception:
        print(f"WARNING: No news found for {ticker} — using placeholder")
        return [
            {
                "headline": f"No recent news found for {ticker}",
                "body": "",
                "source": "none",
                "published_at": "",
            }
        ]

def generate_narrative(ticker: str, company_name: str, articles: list) -> str:
    """Call Claude API to generate a 3-sentence trade brief from the articles."""
    articles_text = "\n".join(
        f"- {a['source']}: {a['headline']}. {a['body']}" for a in articles
    )
    user_content = f"Write a 3-sentence intraday trade brief for {company_name} ({ticker}) listed on NSE India.\n\nToday's news articles:\n{articles_text}\n\nRules:\n- Sentence 1: What happened today and why it matters for the share price. Use specific numbers from the news.\n- Sentence 2: What technical picture a trader would likely see (trend direction, momentum, volume expectation).\n- Sentence 3: Directional bias (BUY or SHORT), the key price level to watch for entry, and the single biggest risk to this trade.\n\nReturn ONLY a JSON object in this exact format, nothing else:\n{{\"narrative\": \"sentence1. sentence2. sentence3.\"}}"

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 400,
        "system": "You are a senior equity analyst at a top Indian brokerage covering NSE-listed companies. Your writing is sharp, specific, and sounds like it was written by a human analyst — not a bot. You always use specific numbers and facts from the news. You never invent data.",
        "messages": [{"role": "user", "content": user_content}],
    }
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        raw = data["content"][0]["text"]
        parsed = json.loads(raw)
        return parsed["narrative"]
    except json.JSONDecodeError:
        return raw
    except Exception as e:
        print(e)
        return "Error generating narrative"

def main():
    """Run trade brief for RELIANCE, INFY, HDFCBANK in sequence."""
    companies = [{"ticker": "RELIANCE", "name": "Reliance Industries"}, {"ticker": "INFY", "name": "Infosys"}, {"ticker": "HDFCBANK", "name": "HDFC Bank"}]
    for c in companies:
        ticker, name = c["ticker"], c["name"]
        print("=" * 60)
        print(f"Company: {name} ({ticker})")
        print("Fetching news...")
        articles = fetch_news(name, ticker)
        print(f"Found {len(articles)} articles")
        print("Generating narrative...")
        narrative = generate_narrative(ticker, name, articles)
        print()
        print("TRADEIQ ANALYST BRIEF:")
        print(narrative)
        print()
        time.sleep(2)


if __name__ == "__main__":
    main()
