"""
main.py — TradeIQ FastAPI application entry point
Run with: uvicorn backend.main:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.health import router as health_router
from backend.routers.regime import router as regime_router
from backend.routers.intel import router as intel_router
from backend.routers.financials import router as financials_router
from backend.db import create_all_tables

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup — create all database tables."""
    print("TradeIQ backend starting...")
    try:
        await create_all_tables()
        print("Database tables ready.")
    except Exception as e:
        print(f"Database startup skipped (fix DATABASE_URL in .env): {e}")
    yield
    print("TradeIQ backend shutting down.")

app = FastAPI(
    title="TradeIQ API",
    version="1.0.0",
    description="NSE India Intraday Trading Intelligence Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(regime_router)
app.include_router(intel_router)
app.include_router(financials_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "TradeIQ API is running", "docs": "/docs"}
