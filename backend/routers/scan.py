"""
scan.py — FastAPI endpoints for Smart Scan Control Panel.
"""

import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/scan", tags=["scan"])


class ScanRequest(BaseModel):
    category: str
    count: int = 20
    save_as_default: bool = False


@router.get("/categories")
async def get_categories():
    """Return all available scan categories with metadata."""
    from backend.data.scan_categories import CATEGORY_META

    return {"categories": CATEGORY_META}


@router.get("/profile")
async def get_profile():
    """Return saved scan profile."""
    from backend.layers.smart_scan import load_profile

    return load_profile()


@router.post("/profile")
async def save_profile_endpoint(profile: dict):
    """Save scan profile."""
    from backend.layers.smart_scan import save_profile

    save_profile(profile)
    return {"status": "saved"}


@router.get("/preview/{category}")
async def preview_category(category: str, count: int = 20):
    """Preview which companies will be scanned for a category."""
    from backend.layers.smart_scan import resolve_category

    companies = resolve_category(category, count)
    return {"category": category, "count": len(companies), "companies": companies}


@router.post("/run")
async def run_scan(request: ScanRequest):
    """
    Run Smart Scan with streaming progress updates.
    Returns Server-Sent Events (SSE) stream.
    """
    from backend.layers.smart_scan import run_smart_scan

    def event_stream():
        for update in run_smart_scan(
            category=request.category,
            count=request.count,
            save_as_default=request.save_as_default,
        ):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/history")
async def get_scan_history():
    """Return last 20 scan runs from profile."""
    from backend.layers.smart_scan import load_profile

    profile = load_profile()
    return {"history": profile.get("run_history", [])}

