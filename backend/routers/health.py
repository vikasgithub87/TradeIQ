"""
health.py — Health check endpoint for Sprint 1 validation
"""
from fastapi import APIRouter
from backend.db import check_db_connection

router = APIRouter()

@router.get("/health")
async def health_check():
    """Return system health — used by validator test s1_1."""
    db_ok = await check_db_connection()
    return {
        "status": "ok",
        "db": "connected" if db_ok else "disconnected",
        "version": "1.0",
        "sprint": "1"
    }
