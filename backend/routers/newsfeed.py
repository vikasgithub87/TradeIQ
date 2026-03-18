"""
newsfeed.py — News-first intelligence endpoints.
"""
import json
import os
import datetime
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/newsfeed", tags=["newsfeed"])

NEWS_FIRST_DIR = "backend/data"


@router.get("/today")
async def get_today_newsfeed():
    """
    Return today's news-first scan result.
    Shows: top headlines, themes, impacted companies, market sentiment.
    """
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filepath = os.path.join(NEWS_FIRST_DIR, f"news_first_{date_str}.json")

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="News-first scan not run yet. Run: python backend/layers/layer1_news_first.py",
        )
    with open(filepath) as f:
        return json.load(f)


@router.post("/run")
async def run_newsfeed(use_claude: bool = True):
    """Trigger news-first scan."""
    try:
        import sys

        sys.path.insert(0, ".")
        from backend.layers.layer1_news_first import run_news_first_scan

        result = run_news_first_scan(use_claude=use_claude)
        return {
            "status": "ok",
            "headline_count": result.get("headline_count", 0),
            "companies_found": result.get("ticker_count", 0),
            "themes": result.get("themes", []),
            "market_sentiment": result.get("market_sentiment", "mixed"),
            "key_risk": result.get("key_risk", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/headlines")
async def get_headlines():
    """Return raw headlines from latest news-first scan."""
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filepath = os.path.join(NEWS_FIRST_DIR, f"news_first_{date_str}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Run /newsfeed/run first")
    with open(filepath) as f:
        data = json.load(f)
    return {
        "date": data.get("date"),
        "headlines": data.get("headlines", []),
        "themes": data.get("themes", []),
        "market_sentiment": data.get("market_sentiment"),
        "key_risk": data.get("key_risk"),
    }

