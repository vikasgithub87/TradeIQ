"""
TradeIQ Sprint Validator
========================
Run this file from your project root:
    python tradeiq_validator.py

Requirements: Python 3.8+ (tkinter is built-in, no pip install needed)
Optional:     pip install requests  (for live API tests)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import subprocess
import threading
import datetime
import sys

# ── colour palette ────────────────────────────────────────────────────────────
BG        = "#1e1e2e"
BG2       = "#2a2a3e"
BG3       = "#313148"
FG        = "#e2e2f0"
FG2       = "#9999bb"
ACCENT    = "#7c7cff"
GREEN     = "#3ddc84"
GREEN_BG  = "#1a3a2a"
RED       = "#ff6b6b"
RED_BG    = "#3a1a1a"
AMBER     = "#ffc947"
AMBER_BG  = "#3a2e10"
BLUE      = "#5bc0eb"
BORDER    = "#3a3a5c"
BTN_BG    = "#3a3a5c"
BTN_FG    = "#e2e2f0"
BTN_HOV   = "#4a4a7c"
MONO      = "Courier New"
SANS      = "Segoe UI" if sys.platform == "win32" else "Helvetica"

RESULTS_FILE = "tradeiq_validator_results.json"

# ── NSE company master — ticker: {name, sector} ───────────────────────────────
NSE_COMPANIES = {
    "RELIANCE":     {"name": "Reliance Industries",          "sector": "Energy"},
    "TCS":          {"name": "Tata Consultancy Services",    "sector": "IT"},
    "HDFCBANK":     {"name": "HDFC Bank",                    "sector": "Banking"},
    "INFY":         {"name": "Infosys",                      "sector": "IT"},
    "ICICIBANK":    {"name": "ICICI Bank",                   "sector": "Banking"},
    "HINDUNILVR":   {"name": "Hindustan Unilever",           "sector": "FMCG"},
    "ITC":          {"name": "ITC Limited",                  "sector": "FMCG"},
    "SBIN":         {"name": "State Bank of India",          "sector": "Banking"},
    "BAJFINANCE":   {"name": "Bajaj Finance",                "sector": "Banking"},
    "BHARTIARTL":   {"name": "Bharti Airtel",                "sector": "Telecom"},
    "KOTAKBANK":    {"name": "Kotak Mahindra Bank",          "sector": "Banking"},
    "LT":           {"name": "Larsen & Toubro",              "sector": "Infra"},
    "ASIANPAINT":   {"name": "Asian Paints",                 "sector": "Chemicals"},
    "AXISBANK":     {"name": "Axis Bank",                    "sector": "Banking"},
    "MARUTI":       {"name": "Maruti Suzuki",                "sector": "Auto"},
    "TITAN":        {"name": "Titan Company",                "sector": "FMCG"},
    "WIPRO":        {"name": "Wipro",                        "sector": "IT"},
    "NESTLEIND":    {"name": "Nestle India",                 "sector": "FMCG"},
    "ULTRACEMCO":   {"name": "UltraTech Cement",             "sector": "Infra"},
    "POWERGRID":    {"name": "Power Grid Corporation",       "sector": "Energy"},
    "NTPC":         {"name": "NTPC Limited",                 "sector": "Energy"},
    "ONGC":         {"name": "Oil & Natural Gas Corporation","sector": "Energy"},
    "TECHM":        {"name": "Tech Mahindra",                "sector": "IT"},
    "HCLTECH":      {"name": "HCL Technologies",             "sector": "IT"},
    "SUNPHARMA":    {"name": "Sun Pharmaceutical",           "sector": "Pharma"},
    "CIPLA":        {"name": "Cipla",                        "sector": "Pharma"},
    "DRREDDY":      {"name": "Dr Reddy's Laboratories",      "sector": "Pharma"},
    "DIVISLAB":     {"name": "Divi's Laboratories",          "sector": "Pharma"},
    "BAJAJFINSV":   {"name": "Bajaj Finserv",                "sector": "Banking"},
    "ADANIPORTS":   {"name": "Adani Ports & SEZ",            "sector": "Infra"},
    "TATAMOTORS":   {"name": "Tata Motors",                  "sector": "Auto"},
    "TATASTEEL":    {"name": "Tata Steel",                   "sector": "Metals"},
    "JSWSTEEL":     {"name": "JSW Steel",                    "sector": "Metals"},
    "HINDALCO":     {"name": "Hindalco Industries",          "sector": "Metals"},
    "COALINDIA":    {"name": "Coal India",                   "sector": "Energy"},
    "GRASIM":       {"name": "Grasim Industries",            "sector": "Chemicals"},
    "BRITANNIA":    {"name": "Britannia Industries",         "sector": "FMCG"},
    "HEROMOTOCO":   {"name": "Hero MotoCorp",                "sector": "Auto"},
    "EICHERMOT":    {"name": "Eicher Motors",                "sector": "Auto"},
    "BPCL":         {"name": "Bharat Petroleum",             "sector": "Energy"},
    "INDUSINDBK":   {"name": "IndusInd Bank",                "sector": "Banking"},
    "M&M":          {"name": "Mahindra & Mahindra",          "sector": "Auto"},
    "ADANIENT":     {"name": "Adani Enterprises",            "sector": "Infra"},
    "APOLLOHOSP":   {"name": "Apollo Hospitals",             "sector": "Pharma"},
    "TATACONSUM":   {"name": "Tata Consumer Products",       "sector": "FMCG"},
    "SBILIFE":      {"name": "SBI Life Insurance",           "sector": "Banking"},
    "HDFCLIFE":     {"name": "HDFC Life Insurance",          "sector": "Banking"},
    "BAJAJ-AUTO":   {"name": "Bajaj Auto",                   "sector": "Auto"},
    "UPL":          {"name": "UPL Limited",                  "sector": "Chemicals"},
    "VEDL":         {"name": "Vedanta Limited",              "sector": "Metals"},
    "PIDILITIND":   {"name": "Pidilite Industries",          "sector": "Chemicals"},
    "GODREJCP":     {"name": "Godrej Consumer Products",     "sector": "FMCG"},
    "DABUR":        {"name": "Dabur India",                  "sector": "FMCG"},
    "MARICO":       {"name": "Marico",                       "sector": "FMCG"},
    "COLPAL":       {"name": "Colgate-Palmolive India",      "sector": "FMCG"},
    "HAVELLS":      {"name": "Havells India",                "sector": "Infra"},
    "VOLTAS":       {"name": "Voltas",                       "sector": "Infra"},
    "BERGEPAINT":   {"name": "Berger Paints",                "sector": "Chemicals"},
    "KANSAINER":    {"name": "Kansai Nerolac Paints",        "sector": "Chemicals"},
    "MUTHOOTFIN":   {"name": "Muthoot Finance",              "sector": "Banking"},
    "CHOLAFIN":     {"name": "Cholamandalam Finance",        "sector": "Banking"},
    "RECLTD":       {"name": "REC Limited",                  "sector": "Banking"},
    "PFC":          {"name": "Power Finance Corporation",    "sector": "Banking"},
    "TATAPOWER":    {"name": "Tata Power",                   "sector": "Energy"},
    "ADANIGREEN":   {"name": "Adani Green Energy",           "sector": "Energy"},
    "ADANITRANS":   {"name": "Adani Transmission",           "sector": "Energy"},
    "IOC":          {"name": "Indian Oil Corporation",       "sector": "Energy"},
    "HINDPETRO":    {"name": "Hindustan Petroleum",          "sector": "Energy"},
    "GAIL":         {"name": "GAIL India",                   "sector": "Energy"},
    "PETRONET":     {"name": "Petronet LNG",                 "sector": "Energy"},
    "ZOMATO":       {"name": "Zomato",                       "sector": "IT"},
    "NYKAA":        {"name": "FSN E-Commerce (Nykaa)",       "sector": "IT"},
    "PAYTM":        {"name": "One97 Communications (Paytm)", "sector": "IT"},
    "POLICYBZR":    {"name": "PB Fintech (PolicyBazaar)",    "sector": "Banking"},
    "DMART":        {"name": "Avenue Supermarts (DMart)",    "sector": "FMCG"},
    "TRENT":        {"name": "Trent (Westside / Zudio)",     "sector": "FMCG"},
    "JUBLFOOD":     {"name": "Jubilant FoodWorks",           "sector": "FMCG"},
    "WESTLIFE":     {"name": "Westlife Foodworld (McDonald's)", "sector": "FMCG"},
    "INDHOTEL":     {"name": "Indian Hotels (Taj)",          "sector": "FMCG"},
    "IRCTC":        {"name": "Indian Railway Catering & Tourism", "sector": "Infra"},
    "IRFC":         {"name": "Indian Railway Finance Corp",  "sector": "Banking"},
    "HAL":          {"name": "Hindustan Aeronautics",        "sector": "Infra"},
    "BEL":          {"name": "Bharat Electronics",           "sector": "Infra"},
    "BHEL":         {"name": "Bharat Heavy Electricals",     "sector": "Infra"},
    "SIEMENS":      {"name": "Siemens India",                "sector": "Infra"},
    "ABB":          {"name": "ABB India",                    "sector": "Infra"},
    "CUMMINSIND":   {"name": "Cummins India",                "sector": "Infra"},
    "AUROPHARMA":   {"name": "Aurobindo Pharma",             "sector": "Pharma"},
    "LUPIN":        {"name": "Lupin",                        "sector": "Pharma"},
    "TORNTPHARM":   {"name": "Torrent Pharmaceuticals",      "sector": "Pharma"},
    "BIOCON":       {"name": "Biocon",                       "sector": "Pharma"},
    "ALKEM":        {"name": "Alkem Laboratories",           "sector": "Pharma"},
    "IPCALAB":      {"name": "IPCA Laboratories",            "sector": "Pharma"},
    "ZYDUSLIFE":    {"name": "Zydus Lifesciences",           "sector": "Pharma"},
    "MOTHERSON":    {"name": "Samvardhana Motherson",        "sector": "Auto"},
    "BALKRISIND":   {"name": "Balkrishna Industries",        "sector": "Auto"},
    "APOLLOTYRE":   {"name": "Apollo Tyres",                 "sector": "Auto"},
    "MRF":          {"name": "MRF",                          "sector": "Auto"},
    "CEAT":         {"name": "CEAT",                         "sector": "Auto"},
    "BOSCHLTD":     {"name": "Bosch India",                  "sector": "Auto"},
    "ESCORT":       {"name": "Escorts Kubota",               "sector": "Auto"},
    "TVSMOTOR":     {"name": "TVS Motor Company",            "sector": "Auto"},
    "ASHOKLEY":     {"name": "Ashok Leyland",                "sector": "Auto"},
    "EXIDEIND":     {"name": "Exide Industries",             "sector": "Auto"},
    "SAIL":         {"name": "Steel Authority of India",     "sector": "Metals"},
    "NATIONALUM":   {"name": "National Aluminium (NALCO)",   "sector": "Metals"},
    "NMDC":         {"name": "NMDC",                         "sector": "Metals"},
    "HINDZINC":     {"name": "Hindustan Zinc",               "sector": "Metals"},
    "APLAPOLLO":    {"name": "APL Apollo Tubes",             "sector": "Metals"},
    "OBEROIRLTY":   {"name": "Oberoi Realty",                "sector": "Realty"},
    "DLF":          {"name": "DLF",                          "sector": "Realty"},
    "GODREJPROP":   {"name": "Godrej Properties",            "sector": "Realty"},
    "PRESTIGE":     {"name": "Prestige Estates",             "sector": "Realty"},
    "BRIGADE":      {"name": "Brigade Enterprises",          "sector": "Realty"},
    "PHOENIXLTD":   {"name": "Phoenix Mills",                "sector": "Realty"},
    "MPHASIS":      {"name": "Mphasis",                      "sector": "IT"},
    "LTIM":         {"name": "LTIMindtree",                  "sector": "IT"},
    "PERSISTENT":   {"name": "Persistent Systems",           "sector": "IT"},
    "COFORGE":      {"name": "Coforge",                      "sector": "IT"},
    "KPITTECH":     {"name": "KPIT Technologies",            "sector": "IT"},
    "TATAELXSI":    {"name": "Tata Elxsi",                   "sector": "IT"},
    "INTELLECT":    {"name": "Intellect Design Arena",       "sector": "IT"},
    "TANLA":        {"name": "Tanla Platforms",              "sector": "IT"},
    "INDIAMART":    {"name": "IndiaMART InterMESH",          "sector": "IT"},
    "NAUKRI":       {"name": "Info Edge (Naukri)",           "sector": "IT"},
    "JUSTDIAL":     {"name": "Just Dial",                    "sector": "IT"},
    "IDEA":         {"name": "Vodafone Idea",                "sector": "Telecom"},
    "TATACOMM":     {"name": "Tata Communications",          "sector": "Telecom"},
    "HFCL":         {"name": "HFCL",                         "sector": "Telecom"},
    "STLTECH":      {"name": "STL — Sterlite Technologies",  "sector": "Telecom"},
    "BANDHANBNK":   {"name": "Bandhan Bank",                 "sector": "Banking"},
    "FEDERALBNK":   {"name": "Federal Bank",                 "sector": "Banking"},
    "IDFCFIRSTB":   {"name": "IDFC First Bank",              "sector": "Banking"},
    "RBLBANK":      {"name": "RBL Bank",                     "sector": "Banking"},
    "YESBANK":      {"name": "Yes Bank",                     "sector": "Banking"},
    "CANBK":        {"name": "Canara Bank",                  "sector": "Banking"},
    "BANKBARODA":   {"name": "Bank of Baroda",               "sector": "Banking"},
    "UNIONBANK":    {"name": "Union Bank of India",          "sector": "Banking"},
    "PNB":          {"name": "Punjab National Bank",         "sector": "Banking"},
    "MANAPPURAM":   {"name": "Manappuram Finance",           "sector": "Banking"},
    "LICHSGFIN":    {"name": "LIC Housing Finance",          "sector": "Banking"},
    "PNBHOUSING":   {"name": "PNB Housing Finance",          "sector": "Banking"},
}

# ── output files produced by each sprint layer ────────────────────────────────
OUTPUT_FILES = [
    {
        "sprint":  "Proof of Concept",
        "label":   "poc_output",
        "display": "Narrative output (terminal)",
        "path":    None,          # terminal only — captured live
        "cmd":     ["python", "poc_script.py"],
        "desc":    "3-sentence analyst brief generated by Claude API",
        "format":  "text",
    },
    {
        "sprint":  "Sprint 2 — Layer 0",
        "label":   "regime_context",
        "display": "regime_context.json",
        "path":    "backend/data/regime_context.json",
        "cmd":     None,
        "desc":    "Today's market regime, VIX, thresholds, Do-Not-Trade flag",
        "format":  "json",
    },
    {
        "sprint":  "Sprint 3 — Layer 1 News",
        "label":   "company_intel_news",
        "display": "company_intel_{TICKER}.json  (news fields)",
        "path":    None,          # user picks ticker
        "cmd":     None,
        "desc":    "Sentiment-scored news catalysts for a company",
        "format":  "json",
        "ticker_picker": True,
        "path_template": "backend/data/company_intel/company_intel_{ticker}_{date}.json",
    },
    {
        "sprint":  "Sprint 4 — Layer 1 Financials",
        "label":   "company_intel_full",
        "display": "company_intel_{TICKER}.json  (full — news + financials)",
        "path":    None,
        "cmd":     None,
        "desc":    "Full intelligence file with earnings, OI, FII, promoter data",
        "format":  "json",
        "ticker_picker": True,
        "path_template": "backend/data/company_intel/company_intel_{ticker}_{date}.json",
    },
    {
        "sprint":  "Sprint 5 — Layer 2 BUY",
        "label":   "trading_scores",
        "display": "trading_scores_{DATE}.json",
        "path":    None,
        "cmd":     None,
        "desc":    "BUY + SHORT scores for all companies, sector theme scores",
        "format":  "json",
        "date_picker": True,
        "path_template": "backend/data/trading_scores_{date}.json",
    },
    {
        "sprint":  "Sprint 6 — Layer 2 SHORT",
        "label":   "trading_scores_short",
        "display": "trading_scores_{DATE}.json  (short signals)",
        "path":    None,
        "cmd":     None,
        "desc":    "Same file as Sprint 5 — look at short_score and short signal columns",
        "format":  "json",
        "date_picker": True,
        "path_template": "backend/data/trading_scores_{date}.json",
    },
    {
        "sprint":  "Sprint 7 — Layer 3",
        "label":   "validated_signals",
        "display": "validated_signals_{DATE}.json",
        "path":    None,
        "cmd":     None,
        "desc":    "Technical validation results — confidence scores, entry/target/SL",
        "format":  "json",
        "date_picker": True,
        "path_template": "backend/data/validated_signals_{date}.json",
    },
    {
        "sprint":  "Sprint 9 — Layer 4",
        "label":   "personality_profile",
        "display": "personality_profile_{TENANT}.json",
        "path":    "backend/data/personality_profile_0001.json",
        "cmd":     None,
        "desc":    "Your trader personality — sector win rates, signal preferences, coaching note",
        "format":  "json",
    },
    {
        "sprint":  "Sprint 11 — Layer 5 Learn",
        "label":   "paper_trades",
        "display": "paper_trades log (DB query)",
        "path":    None,
        "cmd":     ["python", "-c",
                    "import sys,json; sys.path.insert(0,'backend'); from db import get_paper_trades; trades=get_paper_trades('0001',limit=20); print(json.dumps(trades,indent=2,default=str))"],
        "desc":    "Last 20 paper trades — entry, exit, P&L, outcome",
        "format":  "json",
    },
    {
        "sprint":  "Sprint 12 — Feedback Loop",
        "label":   "model_weights",
        "display": "model_weights.json",
        "path":    "backend/data/model_weights_0001.json",
        "cmd":     None,
        "desc":    "Current L2 scoring factor weights after retraining",
        "format":  "json",
    },
]

# ── sprint / test data ────────────────────────────────────────────────────────
SPRINTS = [
    {
        "id": "poc",
        "label": "Proof of Concept",
        "goal": "One Python script fetches news for one company, calls Claude API, prints a 3-sentence trade brief that reads like a real analyst wrote it.",
        "tests": [
            {
                "id": "poc_1",
                "type": "auto",
                "name": "Python 3.8+ installed",
                "desc": "Python version check",
                "auto_cmd": ["python", "--version"],
                "expect": "Python 3",
                "vector": "Run: python --version  →  expect 'Python 3.x.x'"
            },
            {
                "id": "poc_2",
                "type": "auto",
                "name": "requests library available",
                "desc": "Needed for NewsAPI + Claude API calls",
                "auto_cmd": ["python", "-c", "import requests; print('requests ok')"],
                "expect": "requests ok",
                "vector": "python -c 'import requests'  →  no error"
            },
            {
                "id": "poc_3",
                "type": "auto",
                "name": "poc_script.py file exists",
                "desc": "Your proof-of-concept script must exist in project root",
                "auto_cmd": None,
                "file_check": "poc_script.py",
                "vector": "Check file poc_script.py exists in project folder"
            },
            {
                "id": "poc_4",
                "type": "auto",
                "name": "poc_script.py runs without error",
                "desc": "Script executes end-to-end with no exceptions",
                "auto_cmd": ["python", "poc_script.py"],
                "expect": None,
                "expect_no_error": True,
                "vector": "python poc_script.py  →  no traceback, output printed"
            },
            {
                "id": "poc_5",
                "type": "manual",
                "name": "Narrative sounds like a real analyst",
                "desc": "YOU read the output. Does it feel intelligent and specific to the company?",
                "vector": "Run poc_script.py for RELIANCE, INFY, HDFCBANK. Read all 3 outputs. Mark PASS only if all 3 feel like a real analyst wrote them — specific numbers, clear trade direction.",
                "manual_inputs": [
                    {"id": "poc5_notes", "label": "Your notes (what did it say?):", "width": 60}
                ]
            },
            {
                "id": "poc_6",
                "type": "manual",
                "name": "No hallucinated numbers",
                "desc": "Every price/percentage in the narrative came from the actual news",
                "vector": "Compare narrative figures against the actual NewsAPI articles shown. If Claude invented any number not in the source articles, mark FAIL and fix the prompt.",
                "manual_inputs": [
                    {"id": "poc6_notes", "label": "Numbers verified from source? (yes/no + notes):", "width": 60}
                ]
            },
        ],
        "cursor_prompt": """Build a Python proof-of-concept script called poc_script.py that does exactly this:

1. Takes a hardcoded NSE ticker (start with 'RELIANCE')
2. Calls NewsAPI.org (free tier) to fetch the 5 most recent news articles about 'Reliance Industries India'
3. Calls Claude API (claude-sonnet-4-20250514) with this system prompt:
   'You are a senior NSE India equity analyst. Write a 3-sentence intraday trade brief. 
    Sentence 1: what happened today and why it matters for the stock price.
    Sentence 2: what the chart is likely showing (trend, momentum direction).
    Sentence 3: directional bias with entry trigger and key risk.
    Return JSON: { "narrative": "..." }'
4. Prints the narrative to the terminal clearly

Use these environment variables for keys: NEWSAPI_KEY and ANTHROPIC_API_KEY
Handle errors gracefully (print error message, do not crash).
Add a comment at the top showing the expected output format."""
    },
    {
        "id": "sprint1",
        "label": "Sprint 1 — Foundation",
        "goal": "React loads. FastAPI responds. PostgreSQL connected. Auth works. tenant_id on ALL tables.",
        "tests": [
            {
                "id": "s1_1",
                "type": "auto",
                "name": "FastAPI health endpoint",
                "desc": "GET http://localhost:8000/health returns 200 + {status: ok}",
                "auto_cmd": ["python", "-c",
                    "import urllib.request,json; r=urllib.request.urlopen('http://localhost:8000/health'); d=json.loads(r.read()); print('ok' if d.get('status')=='ok' else 'fail')"],
                "expect": "ok",
                "vector": "GET localhost:8000/health  →  {\"status\": \"ok\", \"db\": \"connected\"}"
            },
            {
                "id": "s1_2",
                "type": "auto",
                "name": "FastAPI /docs page accessible",
                "desc": "Swagger UI loads at localhost:8000/docs",
                "auto_cmd": ["python", "-c",
                    "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/docs'); print('ok' if r.status==200 else 'fail')"],
                "expect": "ok",
                "vector": "GET localhost:8000/docs  →  200 OK (Swagger UI)"
            },
            {
                "id": "s1_3",
                "type": "auto",
                "name": "React app accessible",
                "desc": "localhost:3000 returns 200",
                "auto_cmd": ["python", "-c",
                    "import urllib.request; r=urllib.request.urlopen('http://localhost:3000'); print('ok' if r.status==200 else 'fail')"],
                "expect": "ok",
                "vector": "GET localhost:3000  →  200 OK (React app)"
            },
            {
                "id": "s1_4",
                "type": "auto",
                "name": "database_check.py exists and passes",
                "desc": "Your db check script verifies all tables + tenant_id columns",
                "auto_cmd": None,
                "file_check": "database_check.py",
                "vector": "File database_check.py must exist in project root"
            },
            {
                "id": "s1_5",
                "type": "auto",
                "name": "All tables have tenant_id",
                "desc": "Runs database_check.py — every table must have tenant_id UUID column",
                "auto_cmd": ["python", "database_check.py"],
                "expect": "ALL TABLES HAVE TENANT_ID",
                "vector": "python database_check.py  →  prints 'ALL TABLES HAVE TENANT_ID'"
            },
            {
                "id": "s1_6",
                "type": "manual",
                "name": "Full login flow works",
                "desc": "Register → verify email → login → see dashboard → logout → login again",
                "vector": "1. Go to localhost:3000\n2. Click Register\n3. Enter your real email\n4. Check inbox — click Supabase verify link\n5. Login with same email+password\n6. Confirm you see the dashboard\n7. Logout and login again\nAll 7 steps must complete without error.",
                "manual_inputs": [
                    {"id": "s1_6_email", "label": "Email used for test:", "width": 40},
                    {"id": "s1_6_notes", "label": "Any issues encountered:", "width": 60}
                ]
            },
            {
                "id": "s1_7",
                "type": "manual",
                "name": "Network tab shows :8000 requests",
                "desc": "React app is calling FastAPI — verified in browser DevTools",
                "vector": "1. Open localhost:3000 in Chrome\n2. Press F12 → Network tab\n3. Reload the page\n4. Look for requests to localhost:8000\n5. Click one — Status must be 200\n6. Click Response tab — must show JSON data",
                "manual_inputs": [
                    {"id": "s1_7_endpoint", "label": "Which endpoint was called (e.g. /health):", "width": 40},
                    {"id": "s1_7_notes", "label": "Notes:", "width": 60}
                ]
            },
        ],
        "cursor_prompt": """Build Sprint 1 of TradeIQ — a full-stack web application scaffold with these exact components:

BACKEND (Python FastAPI):
- File structure: backend/main.py, backend/db.py, backend/models.py, backend/routers/health.py
- FastAPI app with CORS enabled for localhost:3000
- PostgreSQL connection via SQLAlchemy (async) using DATABASE_URL from .env
- Health endpoint: GET /health returns {"status": "ok", "db": "connected", "version": "1.0"}
- These database tables with SQLAlchemy models (EVERY table must have tenant_id UUID column):
  * users (id, tenant_id, email, created_at)
  * regime_context (id, tenant_id, date, regime, regime_score, do_not_trade, created_at)
  * company_intel (id, tenant_id, ticker, date, data_json, created_at)
  * trading_scores (id, tenant_id, ticker, date, buy_score, short_score, signal, created_at)
  * validated_signals (id, tenant_id, ticker, date, confidence_score, entry_low, entry_high, target_1, stop_loss, direction, created_at)
  * paper_trades (id, tenant_id, ticker, direction, entry_price, target_1, stop_loss, exit_price, pnl_pct, outcome, created_at)
  * personality_profiles (id, tenant_id, profile_json, version, updated_at)
  * model_weights (id, tenant_id, layer, factor_name, weight, updated_at)
- requirements.txt with: fastapi, uvicorn, sqlalchemy, asyncpg, python-dotenv, pydantic

FRONTEND (React + TypeScript):
- Created with: npm create vite@latest frontend -- --template react-ts
- Install: npm install @supabase/supabase-js axios react-router-dom
- File: frontend/src/lib/supabase.ts  — Supabase client using VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
- File: frontend/src/pages/Login.tsx  — Simple login + register form using Supabase Auth
- File: frontend/src/pages/Dashboard.tsx — Protected page showing "TradeIQ Dashboard — Sprint 1 Complete"
- File: frontend/src/App.tsx — Router with public /login route and protected / route
- File: frontend/.env.example — VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL

DATABASE CHECK SCRIPT:
- File: database_check.py in project root
- Connects to PostgreSQL using DATABASE_URL from .env
- Checks every table has tenant_id column
- Prints "ALL TABLES HAVE TENANT_ID" if pass, or lists missing tables if fail

ENV FILES:
- backend/.env.example: DATABASE_URL, ANTHROPIC_API_KEY, NEWSAPI_KEY
- frontend/.env.example: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL=http://localhost:8000

README.md with exact commands to start both servers."""
    },
    {
        "id": "sprint2",
        "label": "Sprint 2 — Layer 0: Regime",
        "goal": "Market regime correctly classified every morning. Do-Not-Trade fires on correct conditions. Scheduler runs at 07:30 IST.",
        "tests": [
            {
                "id": "s2_1",
                "type": "auto",
                "name": "layer0.py file exists",
                "desc": "Layer 0 script must exist in backend/layers/",
                "auto_cmd": None,
                "file_check": "backend/layers/layer0.py",
                "vector": "File backend/layers/layer0.py exists"
            },
            {
                "id": "s2_2",
                "type": "auto",
                "name": "NSE holiday test — Republic Day",
                "desc": "Jan 26 2025 must return market_open=false",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer0 import classify_regime; r=classify_regime('2025-01-26'); print('ok' if not r.get('market_open') else 'fail_market_should_be_closed')"],
                "expect": "ok",
                "vector": "classify_regime('2025-01-26')  →  market_open=false (Republic Day)"
            },
            {
                "id": "s2_3",
                "type": "auto",
                "name": "F&O expiry detection — Jan 30 2025",
                "desc": "Last Thursday of month flagged as expiry",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer0 import classify_regime; r=classify_regime('2025-01-30'); print('ok' if r.get('is_expiry_day') else 'fail_expiry_not_detected')"],
                "expect": "ok",
                "vector": "classify_regime('2025-01-30')  →  is_expiry_day=true"
            },
            {
                "id": "s2_4",
                "type": "auto",
                "name": "High VIX triggers DO_NOT_TRADE",
                "desc": "VIX=29.5 must produce DO_NOT_TRADE regime",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer0 import classify_regime; r=classify_regime('2025-03-15', mock_vix=29.5); print('ok' if r.get('regime')=='DO_NOT_TRADE' else 'fail_got_'+str(r.get('regime')))"],
                "expect": "ok",
                "vector": "classify_regime(mock_vix=29.5)  →  regime='DO_NOT_TRADE'"
            },
            {
                "id": "s2_5",
                "type": "auto",
                "name": "Output JSON has all required fields",
                "desc": "regime_context.json must have 10 required keys",
                "auto_cmd": ["python", "-c",
                    "import sys,json; sys.path.insert(0,'backend'); from layers.layer0 import classify_regime; r=classify_regime('2025-03-15'); keys=['date','regime','regime_score','india_vix','is_expiry_day','is_rbi_day','do_not_trade','signal_threshold_l2','position_size_multiplier','allowed_directions']; missing=[k for k in keys if k not in r]; print('ok' if not missing else 'missing:'+','.join(missing))"],
                "expect": "ok",
                "vector": "All 10 required fields present in output JSON"
            },
            {
                "id": "s2_6",
                "type": "manual",
                "name": "Today's regime makes sense to you",
                "desc": "Run Layer 0 right now. Does the regime match what the market is actually doing today?",
                "vector": "1. Run: python backend/layers/layer0.py\n2. Look at the 'regime' field in the output\n3. Open Nifty chart on any app\n4. Does the regime label match reality?\n   - Market going up broadly = should be TRENDING_BULL\n   - Flat choppy day = RANGE_BOUND\n   - Heavy selling = TRENDING_BEAR\nMark PASS only if regime makes intuitive sense.",
                "manual_inputs": [
                    {"id": "s2_6_regime", "label": "Regime output today:", "width": 30},
                    {"id": "s2_6_nifty", "label": "What Nifty is actually doing:", "width": 50},
                    {"id": "s2_6_match", "label": "Does it match? (yes/no + reason):", "width": 60}
                ]
            },
        ],
        "cursor_prompt": """Build Layer 0 (Market Regime DNA) for TradeIQ backend.

File: backend/layers/layer0.py

Create a function classify_regime(date_str: str, mock_vix: float = None) -> dict that:

1. MARKET CALENDAR:
   - NSE holidays list for 2025-2026 (hardcode key holidays: Republic Day Jan 26, Holi, Good Friday, Ambedkar Jayanti, Independence Day Aug 15, Gandhi Jayanti Oct 2, Diwali, Christmas Dec 25)
   - If date is weekend (Sat/Sun) or NSE holiday: return {market_open: false, regime: 'HOLIDAY'}
   - F&O expiry: last Thursday of every month = is_expiry_day=true

2. VIX FETCHING:
   - If mock_vix provided: use it directly (for testing)
   - Otherwise: try to fetch India VIX from NSE website (https://www.nseindia.com/api/allIndices)
   - If fetch fails: use previous day's cached value from regime_context.json, default 15.0

3. REGIME CLASSIFICATION (in priority order):
   - VIX > 28: DO_NOT_TRADE
   - is_rbi_day or is_budget_day: DO_NOT_TRADE  
   - VIX 20-28: HIGH_VOLATILITY
   - is_expiry_day: EXPIRY_CAUTION
   - VIX < 20 + broad market signals: TRENDING_BULL or TRENDING_BEAR or RANGE_BOUND
   - Default: RANGE_BOUND

4. THRESHOLDS by regime:
   - TRENDING_BULL/BEAR: signal_threshold_l2=60, position_size_multiplier=1.0
   - RANGE_BOUND: signal_threshold_l2=72, position_size_multiplier=0.8
   - HIGH_VOLATILITY: signal_threshold_l2=78, position_size_multiplier=0.5
   - EXPIRY_CAUTION: signal_threshold_l2=80, position_size_multiplier=0.6
   - DO_NOT_TRADE: signal_threshold_l2=999, position_size_multiplier=0.0

5. OUTPUT: Return dict and also save to backend/data/regime_context.json:
{
  "date": "2025-03-15",
  "market_open": true,
  "regime": "TRENDING_BULL",
  "regime_score": 74,
  "india_vix": 13.8,
  "is_expiry_day": false,
  "is_rbi_day": false,
  "is_budget_day": false,
  "do_not_trade": false,
  "signal_threshold_l2": 60,
  "signal_threshold_conf": 60,
  "position_size_multiplier": 1.0,
  "allowed_directions": ["BUY", "SHORT"],
  "regime_reason": "one sentence explanation"
}

6. SCHEDULER ENTRY:
   - Add to backend/scheduler.py: Celery beat task 'run_layer0' at 07:30 Asia/Kolkata every weekday
   - requirements addition: celery, redis

Also create: backend/layers/__init__.py (empty)
Also create: backend/data/ directory with .gitkeep"""
    },
    {
        "id": "sprint3",
        "label": "Sprint 3 — L1: News Pipeline",
        "goal": "Accurate sentiment-scored company intelligence files for 50 companies using real NewsAPI data.",
        "tests": [
            {
                "id": "s3_1",
                "type": "auto",
                "name": "layer1_news.py exists",
                "desc": "Layer 1 news module must exist",
                "auto_cmd": None,
                "file_check": "backend/layers/layer1_news.py",
                "vector": "File backend/layers/layer1_news.py exists"
            },
            {
                "id": "s3_2",
                "type": "auto",
                "name": "NewsAPI returns articles for RELIANCE",
                "desc": "At least 2 articles returned with required fields",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_news import fetch_news; arts=fetch_news('RELIANCE','Reliance Industries India'); print('ok' if len(arts)>=2 and 'headline' in arts[0] else 'fail_got_'+str(len(arts))+'_articles')"],
                "expect": "ok",
                "vector": "fetch_news('RELIANCE')  →  list of ≥2 articles with headline field"
            },
            {
                "id": "s3_3",
                "type": "auto",
                "name": "Sentiment classifies earnings beat correctly",
                "desc": "Known positive headline must return positive sentiment",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_news import analyse_sentiment; r=analyse_sentiment('INFY','Infosys raises FY25 revenue guidance to 5 percent, beats Q3 estimates','Infosys reported strong quarterly results exceeding analyst expectations'); print('ok' if r.get('sentiment')=='positive' else 'fail_got_'+str(r.get('sentiment')))"],
                "expect": "ok",
                "vector": "analyse_sentiment on earnings beat headline  →  sentiment='positive'"
            },
            {
                "id": "s3_4",
                "type": "auto",
                "name": "Sentiment classifies negative news correctly",
                "desc": "Known negative headline must return negative sentiment",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_news import analyse_sentiment; r=analyse_sentiment('HDFCBANK','HDFC Bank faces RBI penalty of 200 crore for compliance violations','Reserve Bank of India imposed a fine on HDFC Bank'); print('ok' if r.get('sentiment')=='negative' else 'fail_got_'+str(r.get('sentiment')))"],
                "expect": "ok",
                "vector": "analyse_sentiment on RBI penalty headline  →  sentiment='negative'"
            },
            {
                "id": "s3_5",
                "type": "auto",
                "name": "company_intel JSON has all required fields",
                "desc": "Full pipeline output has 10 required keys",
                "auto_cmd": ["python", "-c",
                    "import sys,json; sys.path.insert(0,'backend'); from layers.layer1_news import run_layer1_news; r=run_layer1_news('RELIANCE','0001'); keys=['ticker','tenant_id','timestamp','long_catalysts','short_catalysts','net_sentiment_score','dominant_direction','intraday_relevance','sector_code']; missing=[k for k in keys if k not in r]; print('ok' if not missing else 'missing:'+','.join(missing))"],
                "expect": "ok",
                "vector": "run_layer1_news('RELIANCE')  →  all 9 required keys present"
            },
            {
                "id": "s3_6",
                "type": "manual",
                "name": "50-company run completes in reasonable time",
                "desc": "Full batch run for 50 companies should finish in under 10 minutes",
                "vector": "1. Run: python backend/layers/layer1_news.py --batch 50\n2. Watch the terminal output\n3. Check backend/data/company_intel/ folder — should have 50 JSON files\n4. Time the run — should be under 10 minutes\n5. Open 3 random files — check the content looks real",
                "manual_inputs": [
                    {"id": "s3_6_time", "label": "Time taken (minutes):", "width": 20},
                    {"id": "s3_6_files", "label": "Number of files created:", "width": 20},
                    {"id": "s3_6_quality", "label": "Quality looks good? (yes/no):", "width": 30}
                ]
            },
            {
                "id": "s3_7",
                "type": "manual",
                "name": "Today's dominant_direction matches real news",
                "desc": "Compare L1 output for 5 companies vs what you read in the news today",
                "vector": "1. Open Moneycontrol app\n2. Pick 5 companies with news today\n3. Run L1 for each\n4. Compare dominant_direction vs your reading\n5. Need 4/5 correct to PASS",
                "manual_inputs": [
                    {"id": "s3_7_score", "label": "How many out of 5 matched? (e.g. 4/5):", "width": 20},
                    {"id": "s3_7_wrong", "label": "Which company was wrong and why:", "width": 60}
                ]
            },
        ],
        "cursor_prompt": """Build Layer 1 News Pipeline for TradeIQ.

File: backend/layers/layer1_news.py

Functions to create:

1. fetch_news(ticker: str, company_name: str, max_articles: int = 10) -> list
   - Calls NewsAPI.org /v2/everything endpoint
   - Query: '{company_name} India stock NSE'
   - Date range: last 2 days only (from=yesterday)
   - Language: en
   - Sort by: publishedAt
   - Returns list of dicts: {headline, body, source, published_at, url}
   - NEWSAPI_KEY from environment variable
   - On API error: return empty list, print warning

2. analyse_sentiment(ticker: str, headline: str, body: str) -> dict
   - Calls Claude API with Prompt 1 from the TradeIQ spec
   - Returns dict with: sentiment, intensity, impact_type, catalyst_type, price_impact_direction, intraday_relevance, key_fact
   - ANTHROPIC_API_KEY from environment variable
   - Model: claude-sonnet-4-20250514
   - System prompt: 'You are a financial intelligence analyst for NSE India. Return only valid JSON.'

3. run_layer1_news(ticker: str, tenant_id: str) -> dict
   - Orchestrates: fetch_news → analyse_sentiment for each article → aggregate
   - Separates long_catalysts (positive) from short_catalysts (negative)
   - Calculates net_sentiment_score: weighted average of all intensities with direction
   - Determines dominant_direction: LONG if net > 0.1, SHORT if net < -0.1, else NEUTRAL
   - Saves to: backend/data/company_intel/company_intel_{ticker}_{date}.json
   - Returns the full dict

4. CLI batch runner at bottom:
   if __name__ == '__main__':
       import argparse
       parser.add_argument('--ticker', default='RELIANCE')
       parser.add_argument('--batch', type=int, help='Run for N companies from watchlist')
       - If --batch: load tickers from backend/data/watchlist.json, run for each
       - Print progress: 'Processing 1/50: RELIANCE...'

WATCHLIST FILE:
Create backend/data/watchlist.json with 50 major NSE tickers:
["RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","HINDUNILVR","ITC","SBIN","BAJFINANCE",
"BHARTIARTL","KOTAKBANK","LT","ASIANPAINT","AXISBANK","MARUTI","TITAN","WIPRO","NESTLEIND",
"ULTRACEMCO","POWERGRID","NTPC","ONGC","TECHM","HCLTECH","SUNPHARMA","CIPLA","DRREDDY",
"DIVISLAB","BAJAJFINSV","ADANIPORTS","TATAMOTORS","TATASTEEL","JSWSTEEL","HINDALCO",
"COALINDIA","GRASIM","BRITANNIA","HEROMOTOCO","EICHERMOT","BPCL","INDUSINDBK","M&M",
"ADANIENT","APOLLOHOSP","TATACONSUM","SBILIFE","HDFCLIFE","BAJAJ-AUTO","UPL","VEDL"]"""
    },
    {
        "id": "sprint4",
        "label": "Sprint 4 — L1: Financial Data",
        "goal": "Full company_intel files with quarterly results, OI data, FII flows, earnings surprise calculated correctly.",
        "tests": [
            {
                "id": "s4_1",
                "type": "auto",
                "name": "yfinance returns NSE data for RELIANCE.NS",
                "desc": "5-minute OHLCV data with > 50 rows returned",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_financials import fetch_intraday; data=fetch_intraday('RELIANCE'); print('ok' if len(data)>10 else 'fail_only_'+str(len(data))+'_rows')"],
                "expect": "ok",
                "vector": "fetch_intraday('RELIANCE')  →  DataFrame with >10 rows of OHLCV data"
            },
            {
                "id": "s4_2",
                "type": "auto",
                "name": "Earnings surprise calculation — beat",
                "desc": "actual=52.3, estimate=48.1 → surprise=+8.7%",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_financials import calc_earnings_surprise; r=calc_earnings_surprise(52.3,48.1); diff=abs(r-8.72); print('ok' if diff<0.1 else 'fail_got_'+str(round(r,2)))"],
                "expect": "ok",
                "vector": "calc_earnings_surprise(52.3, 48.1)  →  8.72 (within 0.1)"
            },
            {
                "id": "s4_3",
                "type": "auto",
                "name": "Earnings surprise calculation — miss",
                "desc": "actual=44.2, estimate=49.0 → surprise=-9.8%",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_financials import calc_earnings_surprise; r=calc_earnings_surprise(44.2,49.0); diff=abs(r-(-9.8)); print('ok' if diff<0.1 else 'fail_got_'+str(round(r,2)))"],
                "expect": "ok",
                "vector": "calc_earnings_surprise(44.2, 49.0)  →  -9.79 (within 0.1)"
            },
            {
                "id": "s4_4",
                "type": "auto",
                "name": "PCR calculation correct",
                "desc": "put_oi=1240000, call_oi=1850000 → PCR=0.67",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer1_financials import calc_pcr; r=calc_pcr(1240000,1850000); diff=abs(r-0.6703); print('ok' if diff<0.01 else 'fail_got_'+str(round(r,4)))"],
                "expect": "ok",
                "vector": "calc_pcr(1240000, 1850000)  →  0.6703 (within 0.01)"
            },
            {
                "id": "s4_5",
                "type": "auto",
                "name": "Full company_intel file has financial fields",
                "desc": "oi_data, promoter_pledge_pct, fii_activity, earnings all present",
                "auto_cmd": ["python", "-c",
                    "import sys,json; sys.path.insert(0,'backend'); from layers.layer1_financials import run_layer1_financials; r=run_layer1_financials('INFY','0001'); keys=['oi_data','promoter_pledge_pct','fii_activity','earnings']; missing=[k for k in keys if k not in r]; print('ok' if not missing else 'missing:'+','.join(missing))"],
                "expect": "ok",
                "vector": "run_layer1_financials('INFY')  →  all 4 financial keys present"
            },
            {
                "id": "s4_6",
                "type": "manual",
                "name": "Earnings surprise matches financial media",
                "desc": "Find a recently-reported company. Compare our eps_surprise_pct to ET/Moneycontrol.",
                "vector": "1. Find a company that reported results in last 2 weeks\n2. Run: python backend/layers/layer1_financials.py --ticker XXXX\n3. Note the eps_surprise_pct value\n4. Check Economic Times or Moneycontrol for the same company result\n5. Our value should be within 2% of what they report",
                "manual_inputs": [
                    {"id": "s4_6_ticker", "label": "Company tested:", "width": 20},
                    {"id": "s4_6_our", "label": "Our eps_surprise_pct:", "width": 20},
                    {"id": "s4_6_media", "label": "ET/Moneycontrol reported:", "width": 20},
                    {"id": "s4_6_match", "label": "Within 2%? (yes/no):", "width": 20}
                ]
            },
        ],
        "cursor_prompt": """Build Layer 1 Financial Data module for TradeIQ.

File: backend/layers/layer1_financials.py

Functions to create:

1. fetch_intraday(ticker: str, interval: str = '5m', period: str = '1d') -> pd.DataFrame
   - Uses yfinance: yf.download(ticker+'.NS', period=period, interval=interval)
   - Returns DataFrame with columns: Open, High, Low, Close, Volume
   - On error: return empty DataFrame

2. fetch_fundamentals(ticker: str) -> dict
   - Uses yfinance: yf.Ticker(ticker+'.NS').info
   - Returns: {market_cap, pe_ratio, debt_to_equity, promoter_holding_pct}
   - On error: return dict with None values

3. calc_earnings_surprise(actual: float, estimate: float) -> float
   - Returns: ((actual - estimate) / abs(estimate)) * 100
   - Rounded to 2 decimal places

4. calc_pcr(put_oi: float, call_oi: float) -> float
   - Returns: put_oi / call_oi rounded to 4 decimal places
   - Returns 1.0 if call_oi is 0

5. fetch_oi_data(ticker: str) -> dict
   - Download NSE F&O data (use NSE bhavcopy URL or mock with realistic values for now)
   - Returns: {total_put_oi, total_call_oi, pcr, oi_signal: 'long_buildup|short_buildup|neutral'}
   - oi_signal logic: pcr > 1.2 = long_buildup, pcr < 0.6 = short_buildup, else neutral

6. run_layer1_financials(ticker: str, tenant_id: str) -> dict
   - Orchestrates all financial data fetching
   - Merges with existing company_intel file if it exists (from layer1_news.py)
   - Adds these fields to the company_intel dict:
     * oi_data: {pcr, oi_signal, total_put_oi, total_call_oi}
     * promoter_pledge_pct: float (0.0 if not available)
     * fii_activity: 'net_buyer' | 'net_seller' | 'neutral' (mock from FII data)
     * earnings: {announced, eps_surprise_pct, guidance, surprise_label}
     * fundamentals: {market_cap, pe_ratio}
   - Saves updated file to backend/data/company_intel/
   - Returns the merged dict

7. CLI at bottom:
   --ticker argument to run for single company
   Prints the financial summary to console

requirements additions: yfinance, pandas, numpy"""
    },
    {
        "id": "sprint5",
        "label": "Sprint 5 — L2: BUY Scores",
        "goal": "Ranked BUY scores for all NSE companies. Top 20 manually verified. Regime threshold filter works.",
        "tests": [
            {
                "id": "s5_1",
                "type": "auto",
                "name": "layer2_scoring.py exists",
                "desc": "Layer 2 scoring module must exist",
                "auto_cmd": None,
                "file_check": "backend/layers/layer2_scoring.py",
                "vector": "File backend/layers/layer2_scoring.py exists"
            },
            {
                "id": "s5_2",
                "type": "auto",
                "name": "Score range validation — all scores 0-100",
                "desc": "No score outside valid range, no NaN values",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer2_scoring import calculate_buy_score; scores=[calculate_buy_score({'ticker':'T'+str(i),'net_sentiment_score':0.5,'earnings':{'eps_surprise_pct':5},'oi_data':{'pcr':1.1},'fii_activity':'net_buyer','google_trends_spike':True}) for i in range(5)]; valid=all(0<=s<=100 for s in scores if s is not None); print('ok' if valid else 'fail_scores:'+str(scores))"],
                "expect": "ok",
                "vector": "5 sample score calls  →  all results between 0 and 100"
            },
            {
                "id": "s5_3",
                "type": "auto",
                "name": "Strong positive input scores > 70",
                "desc": "All factors at maximum should produce high score",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer2_scoring import calculate_buy_score; data={'ticker':'TEST','net_sentiment_score':0.95,'earnings':{'eps_surprise_pct':15,'guidance':'raised'},'oi_data':{'pcr':1.4,'oi_signal':'long_buildup'},'fii_activity':'net_buyer','google_trends_spike':True,'promoter_activity':'buying'}; s=calculate_buy_score(data); print('ok' if s>70 else 'fail_score_too_low:'+str(s))"],
                "expect": "ok",
                "vector": "All-positive inputs  →  score > 70"
            },
            {
                "id": "s5_4",
                "type": "auto",
                "name": "Regime threshold filter removes low scores",
                "desc": "Companies below threshold must not appear in filtered output",
                "auto_cmd": ["python", "-c",
                    "import sys; sys.path.insert(0,'backend'); from layers.layer2_scoring import filter_by_regime; scores=[{'ticker':'A','buy_score':80},{'ticker':'B','buy_score':50},{'ticker':'C','buy_score':65}]; filtered=filter_by_regime(scores,threshold=65); tickers=[s['ticker'] for s in filtered]; print('ok' if 'B' not in tickers and 'A' in tickers else 'fail_tickers:'+str(tickers))"],
                "expect": "ok",
                "vector": "filter_by_regime(threshold=65) removes score=50, keeps score=65 and 80"
            },
            {
                "id": "s5_5",
                "type": "manual",
                "name": "Backtesting accuracy — 3 of 5 correct",
                "desc": "Top 5 scorers for a past day — did those stocks actually move significantly that day?",
                "vector": "1. Pick any trading day from last month\n2. Collect that day's news and run through L1+L2\n3. Note the top 5 BUY scores\n4. Check those stocks' actual price move that day on TradingView or Moneycontrol\n5. Count how many had a significant positive move (>1%)\n6. Need 3/5 to PASS",
                "manual_inputs": [
                    {"id": "s5_5_date", "label": "Date tested:", "width": 20},
                    {"id": "s5_5_top5", "label": "Top 5 tickers + scores:", "width": 50},
                    {"id": "s5_5_moved", "label": "How many actually moved >1% up? (x/5):", "width": 20}
                ]
            },
            {
                "id": "s5_6",
                "type": "manual",
                "name": "Today's scores make intuitive sense",
                "desc": "Every company scoring >70 today should have a visible news catalyst",
                "vector": "1. Run L2 scoring right now\n2. Look at all companies scoring > 70\n3. For each one, check Moneycontrol\n4. Every high scorer should have news, FII buying, or results\n5. If any company scores 80+ with zero news — weights need fixing",
                "manual_inputs": [
                    {"id": "s5_6_count", "label": "Companies scoring > 70:", "width": 10},
                    {"id": "s5_6_unexplained", "label": "Any unexplained high scores? (ticker + score):", "width": 50}
                ]
            },
        ],
        "cursor_prompt": """Build Layer 2 BUY Scoring Engine for TradeIQ.

File: backend/layers/layer2_scoring.py

Functions to create:

1. calculate_buy_score(company_intel: dict) -> float
   Uses 8 factors with these weights (total = 100 points):
   - news_sentiment (22pts): net_sentiment_score mapped to 0-22 (score=22 if net=1.0, score=0 if net<=0)
   - earnings_surprise (18pts): eps_surprise_pct — 18pts for >10% beat, 14 for 5-10%, 8 for 2-5%, 0 for miss
     Bonus +3 if guidance='raised'
   - product_launch (14pts): 14 if 'product_launch' in long_catalysts, else 0
   - fii_activity (14pts): 14 if net_buyer, 0 if neutral, -5 if net_seller (capped at 0)
   - sector_tailwind (12pts): passed in separately, 0-12
   - google_trends (10pts): 10 if google_trends_spike=True, 0 if False
   - promoter_activity (6pts): 6 if buying, 0 if neutral, -3 if selling (capped at 0)
   - oi_buildup (4pts): 4 if oi_signal='long_buildup' and pcr>1.2, else 0
   Returns total capped to range [0, 100]

2. calculate_short_score(company_intel: dict) -> float
   Uses 7 factors (separate model, different weights):
   - negative_news (25pts): abs(net_sentiment_score) mapped to 0-25 (only if net < 0)
   - earnings_miss (20pts): abs(eps_surprise_pct) — 20pts for >10% miss, 15 for 5-10%, 8 for 2-5%
     Bonus +3 if guidance='cut'
   - fii_selling (15pts): 15 if net_seller, 0 otherwise
   - oi_short_buildup (15pts): 15 if pcr<0.5, 10 if pcr<0.6, 5 if pcr<0.7, 0 otherwise
   - promoter_pledge (12pts): 12 if pledge_pct>30%, 8 if >20%, 4 if >10%, 0 otherwise
   - sector_headwind (8pts): passed in separately
   - exhaustion_signal (5pts): 5 if price near 52-week high AND negative news
   Returns total capped to range [0, 100]

3. filter_by_regime(scores: list, threshold: int) -> list
   Returns only scores where buy_score >= threshold or short_score >= threshold
   Sorts by max(buy_score, short_score) descending

4. calculate_theme_scores(all_scores: list, sector_map: dict) -> list
   Groups companies by sector, averages their scores
   Returns list of: {sector, buy_score, short_score, signal, top_companies}

5. run_layer2(tenant_id: str = '0001') -> dict
   - Load all company_intel files from backend/data/company_intel/
   - Load regime_context.json for today's threshold
   - Calculate buy_score and short_score for each company
   - Filter by regime threshold
   - Calculate theme scores
   - Determine signal per company: avoid|watch|moderate_buy|buy|strong_buy (and short equivalents)
   - Save to backend/data/trading_scores_{date}.json
   - Returns the full scores dict

6. CLI: --date argument, --ticker for single company
   Pretty-print top 10 buy and top 5 short candidates

SECTOR MAP file: backend/data/sector_map.json
Create with NSE sectors for each ticker in watchlist.json"""
    },
]

# ── main application ──────────────────────────────────────────────────────────

class TradeIQValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("TradeIQ Sprint Validator")
        self.root.geometry("1100x720")
        self.root.configure(bg=BG)
        self.root.minsize(900, 600)

        self.results = self._load_results()
        self.current_sprint_idx = 0
        self.manual_inputs = {}
        self._build_ui()
        self._show_sprint(0)

    # ── persistence ───────────────────────────────────────────────────────────
    def _load_results(self):
        if os.path.exists(RESULTS_FILE):
            try:
                with open(RESULTS_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_results(self):
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump(self.results, f, indent=2)
        except Exception:
            pass

    # ── ui build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # top bar
        topbar = tk.Frame(self.root, bg=BG2, height=50)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="TradeIQ Sprint Validator",
                 bg=BG2, fg=FG, font=(SANS, 14, "bold")).pack(side="left", padx=16, pady=12)

        self.overall_label = tk.Label(topbar, text="", bg=BG2, fg=FG2,
                                       font=(SANS, 11))
        self.overall_label.pack(side="right", padx=16)

        self.save_label = tk.Label(topbar, text="", bg=BG2, fg=GREEN,
                                    font=(SANS, 10))
        self.save_label.pack(side="right", padx=8)

        # main area
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        # left sidebar
        sidebar_frame = tk.Frame(main, bg=BG2, width=220)
        sidebar_frame.pack(side="left", fill="y")
        sidebar_frame.pack_propagate(False)

        tk.Label(sidebar_frame, text="SPRINTS", bg=BG2, fg=FG2,
                 font=(SANS, 9, "bold")).pack(anchor="w", padx=12, pady=(14, 6))

        self.sprint_btns = []
        for i, s in enumerate(SPRINTS):
            btn = tk.Button(
                sidebar_frame,
                text=s["label"],
                bg=BG2, fg=FG,
                font=(SANS, 10),
                relief="flat",
                anchor="w",
                padx=12,
                cursor="hand2",
                command=lambda idx=i: self._show_sprint(idx)
            )
            btn.pack(fill="x", pady=1)
            self.sprint_btns.append(btn)

        # ── Results Viewer button ─────────────────────────────────────────────
        tk.Frame(sidebar_frame, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(12, 4))
        tk.Label(sidebar_frame, text="TOOLS", bg=BG2, fg=FG2,
                 font=(SANS, 9, "bold")).pack(anchor="w", padx=12, pady=(4, 4))
        self.results_viewer_btn = tk.Button(
            sidebar_frame,
            text="Results Viewer",
            bg=BTN_BG, fg=BLUE,
            font=(SANS, 10),
            relief="flat", anchor="w", padx=12,
            cursor="hand2",
            command=self._show_results_viewer
        )
        self.results_viewer_btn.pack(fill="x", pady=1)

        # report button at bottom of sidebar
        tk.Frame(sidebar_frame, bg=BORDER, height=1).pack(fill="x", padx=8, pady=8)
        tk.Button(
            sidebar_frame,
            text="Copy Failure Report",
            bg=BTN_BG, fg=AMBER,
            font=(SANS, 9),
            relief="flat",
            cursor="hand2",
            command=self._copy_failure_report
        ).pack(fill="x", padx=8, pady=2)

        tk.Button(
            sidebar_frame,
            text="Reset All Results",
            bg=BTN_BG, fg=RED,
            font=(SANS, 9),
            relief="flat",
            cursor="hand2",
            command=self._reset_all
        ).pack(fill="x", padx=8, pady=2)

        # right content
        self.content = tk.Frame(main, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._update_sidebar_badges()
        self._update_overall_label()

    # ── sprint display ────────────────────────────────────────────────────────
    def _show_sprint(self, idx):
        self.current_sprint_idx = idx
        for w in self.content.winfo_children():
            w.destroy()
        self.manual_inputs = {}

        # highlight selected sidebar button
        for i, btn in enumerate(self.sprint_btns):
            btn.configure(bg=ACCENT if i == idx else BG2,
                          fg=BG if i == idx else FG)

        sprint = SPRINTS[idx]

        # scrollable canvas
        canvas = tk.Canvas(self.content, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient="vertical",
                                  command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        canvas_win = canvas.create_window((0, 0), window=inner,
                                          anchor="nw", tags="inner")

        def _on_resize(event):
            canvas.itemconfig(canvas_win, width=event.width)
        canvas.bind("<Configure>", _on_resize)

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _on_frame_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        pad = 20

        # sprint header
        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", padx=pad, pady=(pad, 6))

        passed = sum(1 for t in sprint["tests"]
                     if self.results.get(t["id"], {}).get("status") == "pass")
        total = len(sprint["tests"])
        pct = int(passed / total * 100) if total else 0
        status_color = GREEN if passed == total else (AMBER if passed > 0 else RED)

        tk.Label(hdr, text=sprint["label"], bg=BG, fg=FG,
                 font=(SANS, 15, "bold")).pack(side="left")
        tk.Label(hdr, text=f"{passed}/{total}  ({pct}%)",
                 bg=BG, fg=status_color,
                 font=(SANS, 12, "bold")).pack(side="right")

        # progress bar
        pb_frame = tk.Frame(inner, bg=BG3, height=6)
        pb_frame.pack(fill="x", padx=pad, pady=(0, 4))
        pb_frame.pack_propagate(False)
        fill_w = int(pct / 100 * (self.content.winfo_width() - 2 * pad))
        pb_fill = tk.Frame(pb_frame, bg=status_color, height=6)
        pb_fill.place(x=0, y=0, relwidth=pct / 100, relheight=1)

        # goal
        goal_frame = tk.Frame(inner, bg=BG2)
        goal_frame.pack(fill="x", padx=pad, pady=(0, 12))
        tk.Label(goal_frame, text="Sprint goal:",
                 bg=BG2, fg=ACCENT, font=(SANS, 9, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
        tk.Label(goal_frame, text=sprint["goal"],
                 bg=BG2, fg=FG, font=(SANS, 10),
                 wraplength=700, justify="left").pack(anchor="w", padx=10, pady=(2, 8))

        # tests
        tk.Label(inner, text="TESTS", bg=BG, fg=FG2,
                 font=(SANS, 9, "bold")).pack(anchor="w", padx=pad, pady=(4, 4))

        for test in sprint["tests"]:
            self._build_test_card(inner, test, pad)

        # cursor prompt section
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=pad, pady=12)
        self._build_cursor_prompt_section(inner, sprint, pad)

        # gate
        self._build_gate_section(inner, sprint, pad)

    def _build_test_card(self, parent, test, pad):
        status = self.results.get(test["id"], {}).get("status", "pending")
        color_map = {
            "pass": (GREEN_BG, GREEN, "PASS"),
            "fail": (RED_BG, RED, "FAIL"),
            "pending": (BG2, FG2, "—")
        }
        card_bg, status_color, status_text = color_map[status]

        card = tk.Frame(parent, bg=card_bg, relief="flat")
        card.pack(fill="x", padx=pad, pady=3)

        # top row
        top = tk.Frame(card, bg=card_bg)
        top.pack(fill="x", padx=12, pady=(10, 0))

        type_badge_color = BLUE if test["type"] == "auto" else AMBER
        type_label = "AUTO" if test["type"] == "auto" else "MANUAL"
        tk.Label(top, text=f" {type_label} ", bg=type_badge_color,
                 fg=BG, font=(SANS, 8, "bold")).pack(side="left")

        tk.Label(top, text=f"  {test['name']}", bg=card_bg, fg=FG,
                 font=(SANS, 10, "bold")).pack(side="left")

        status_lbl = tk.Label(top, text=f"  {status_text}  ",
                               bg=card_bg, fg=status_color,
                               font=(SANS, 10, "bold"))
        status_lbl.pack(side="right")

        # desc
        tk.Label(card, text=test["desc"], bg=card_bg, fg=FG2,
                 font=(SANS, 9)).pack(anchor="w", padx=12, pady=(2, 0))

        # vector box
        vec_frame = tk.Frame(card, bg=BG3)
        vec_frame.pack(fill="x", padx=12, pady=6)
        tk.Label(vec_frame, text="Test vector:", bg=BG3, fg=ACCENT,
                 font=(MONO, 8, "bold")).pack(anchor="w", padx=8, pady=(4, 0))
        tk.Label(vec_frame, text=test["vector"], bg=BG3, fg=FG,
                 font=(MONO, 9), wraplength=680, justify="left").pack(
                     anchor="w", padx=8, pady=(0, 6))

        # output box for auto tests
        output_var = None
        if test["type"] == "auto":
            out_frame = tk.Frame(card, bg=card_bg)
            out_frame.pack(fill="x", padx=12, pady=(0, 4))
            output_var = tk.StringVar(value=self.results.get(test["id"], {}).get("output", ""))
            out_lbl = tk.Label(out_frame, textvariable=output_var,
                                bg=BG3, fg=FG, font=(MONO, 9),
                                wraplength=680, justify="left",
                                anchor="w")
            out_lbl.pack(fill="x", padx=0, pady=0, ipady=4, ipadx=8)

        # manual inputs
        if test.get("manual_inputs"):
            for mi in test["manual_inputs"]:
                mi_frame = tk.Frame(card, bg=card_bg)
                mi_frame.pack(fill="x", padx=12, pady=2)
                tk.Label(mi_frame, text=mi["label"], bg=card_bg, fg=FG2,
                         font=(SANS, 9)).pack(side="left")
                saved_val = self.results.get(test["id"], {}).get(mi["id"], "")
                var = tk.StringVar(value=saved_val)
                entry = tk.Entry(mi_frame, textvariable=var,
                                 bg=BG3, fg=FG,
                                 insertbackground=FG,
                                 font=(SANS, 9),
                                 relief="flat",
                                 width=mi.get("width", 40))
                entry.pack(side="left", padx=6)
                self.manual_inputs[mi["id"]] = var

        # buttons row
        btn_row = tk.Frame(card, bg=card_bg)
        btn_row.pack(fill="x", padx=12, pady=(4, 10))

        if test["type"] == "auto":
            run_btn = tk.Button(
                btn_row,
                text="▶  Run Test",
                bg=BTN_BG, fg=FG,
                font=(SANS, 9),
                relief="flat",
                cursor="hand2",
                padx=8, pady=3,
                command=lambda t=test, s=status_lbl, o=output_var: self._run_auto_test(t, s, o)
            )
            run_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="✓  Mark Pass",
            bg=GREEN_BG, fg=GREEN,
            font=(SANS, 9), relief="flat",
            cursor="hand2", padx=8, pady=3,
            command=lambda t=test, s=status_lbl: self._mark(t["id"], "pass", s)
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            btn_row, text="✗  Mark Fail",
            bg=RED_BG, fg=RED,
            font=(SANS, 9), relief="flat",
            cursor="hand2", padx=8, pady=3,
            command=lambda t=test, s=status_lbl: self._mark(t["id"], "fail", s)
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            btn_row, text="Reset",
            bg=BTN_BG, fg=FG2,
            font=(SANS, 9), relief="flat",
            cursor="hand2", padx=8, pady=3,
            command=lambda t=test, s=status_lbl: self._mark(t["id"], "pending", s)
        ).pack(side="left")

    def _build_cursor_prompt_section(self, parent, sprint, pad):
        tk.Label(parent, text="CURSOR BUILD PROMPT — copy this into Cursor AI to build this sprint",
                 bg=BG, fg=ACCENT, font=(SANS, 9, "bold")).pack(anchor="w", padx=pad, pady=(0, 4))

        prompt_frame = tk.Frame(parent, bg=BG3)
        prompt_frame.pack(fill="x", padx=pad, pady=(0, 8))

        txt = scrolledtext.ScrolledText(
            prompt_frame,
            bg=BG3, fg=FG,
            font=(MONO, 9),
            height=8,
            relief="flat",
            wrap="word",
            insertbackground=FG
        )
        txt.insert("1.0", sprint["cursor_prompt"])
        txt.configure(state="disabled")
        txt.pack(fill="x", padx=1, pady=1)

        tk.Button(
            parent,
            text="Copy Cursor Prompt to Clipboard",
            bg=ACCENT, fg=BG,
            font=(SANS, 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10, pady=5,
            command=lambda p=sprint["cursor_prompt"]: self._copy_to_clipboard(p)
        ).pack(anchor="w", padx=pad, pady=(0, 8))

    def _build_gate_section(self, parent, sprint, pad):
        passed = sum(1 for t in sprint["tests"]
                     if self.results.get(t["id"], {}).get("status") == "pass")
        total = len(sprint["tests"])
        all_pass = passed == total
        any_fail = any(self.results.get(t["id"], {}).get("status") == "fail"
                       for t in sprint["tests"])

        gate_bg = GREEN_BG if all_pass else (RED_BG if any_fail else AMBER_BG)
        gate_fg = GREEN if all_pass else (RED if any_fail else AMBER)

        if all_pass:
            gate_text = f"All {total} tests passing. Sprint complete. Proceed to the next sprint."
        elif any_fail:
            fail_names = [t["name"] for t in sprint["tests"]
                          if self.results.get(t["id"], {}).get("status") == "fail"]
            gate_text = f"Failing: {', '.join(fail_names)}. Fix these before proceeding."
        else:
            gate_text = f"{total - passed} tests still pending. Complete all tests before proceeding."

        gate_frame = tk.Frame(parent, bg=gate_bg)
        gate_frame.pack(fill="x", padx=pad, pady=(4, 20))

        tk.Label(gate_frame, text="SPRINT GATE", bg=gate_bg, fg=gate_fg,
                 font=(SANS, 9, "bold")).pack(anchor="w", padx=12, pady=(8, 0))
        tk.Label(gate_frame, text=gate_text, bg=gate_bg, fg=FG,
                 font=(SANS, 10), wraplength=700, justify="left").pack(
                     anchor="w", padx=12, pady=(2, 8))

    # ── test execution ────────────────────────────────────────────────────────
    def _run_auto_test(self, test, status_lbl, output_var):
        status_lbl.configure(text=" RUNNING... ", fg=AMBER)
        self.root.update()

        def _run():
            result = "pending"
            output = ""
            try:
                if test.get("file_check"):
                    exists = os.path.exists(test["file_check"])
                    result = "pass" if exists else "fail"
                    output = f"File found: {test['file_check']}" if exists else f"File NOT found: {test['file_check']}"
                elif test.get("auto_cmd"):
                    proc = subprocess.run(
                        test["auto_cmd"],
                        capture_output=True, text=True, timeout=30
                    )
                    raw_out = (proc.stdout or "").strip()
                    raw_err = (proc.stderr or "").strip()
                    output = raw_out if raw_out else raw_err

                    if test.get("expect_no_error"):
                        result = "pass" if proc.returncode == 0 else "fail"
                        if proc.returncode != 0:
                            output = raw_err or "Non-zero exit code"
                    elif test.get("expect"):
                        result = "pass" if test["expect"] in raw_out else "fail"
                    else:
                        result = "pass" if proc.returncode == 0 else "fail"
                else:
                    output = "No command defined for this test"
                    result = "pending"
            except subprocess.TimeoutExpired:
                result = "fail"
                output = "TIMEOUT — test took longer than 30 seconds"
            except FileNotFoundError:
                result = "fail"
                output = f"Command not found: {test['auto_cmd'][0]}"
            except Exception as e:
                result = "fail"
                output = f"Error: {str(e)}"

            self.root.after(0, lambda: self._finish_auto_test(
                test["id"], result, output, status_lbl, output_var))

        threading.Thread(target=_run, daemon=True).start()

    def _finish_auto_test(self, test_id, result, output, status_lbl, output_var):
        self._mark(test_id, result, status_lbl)
        if output_var is not None:
            truncated = output[:200] + "..." if len(output) > 200 else output
            output_var.set(f"Output: {truncated}")
        if test_id not in self.results:
            self.results[test_id] = {}
        self.results[test_id]["output"] = output
        self._save_results()

    # ── state management ──────────────────────────────────────────────────────
    def _mark(self, test_id, status, status_lbl):
        if test_id not in self.results:
            self.results[test_id] = {}
        self.results[test_id]["status"] = status
        self.results[test_id]["timestamp"] = datetime.datetime.now().isoformat()

        # save manual input values
        for mi_id, var in self.manual_inputs.items():
            self.results[test_id][mi_id] = var.get()

        color_map = {
            "pass": (GREEN, " PASS "),
            "fail": (RED, " FAIL "),
            "pending": (FG2, "  —  ")
        }
        fg, text = color_map.get(status, (FG2, "  —  "))
        status_lbl.configure(text=text, fg=fg)

        self._save_results()
        self._update_sidebar_badges()
        self._update_overall_label()
        self._show_saved_indicator()

    def _update_sidebar_badges(self):
        for i, (btn, sprint) in enumerate(zip(self.sprint_btns, SPRINTS)):
            passed = sum(1 for t in sprint["tests"]
                         if self.results.get(t["id"], {}).get("status") == "pass")
            total = len(sprint["tests"])
            any_fail = any(self.results.get(t["id"], {}).get("status") == "fail"
                           for t in sprint["tests"])

            if passed == total:
                bg = "#1a3a2a" if i != self.current_sprint_idx else ACCENT
                fg = GREEN if i != self.current_sprint_idx else BG
                suffix = f" ✓"
            elif any_fail:
                bg = "#3a1a1a" if i != self.current_sprint_idx else ACCENT
                fg = RED if i != self.current_sprint_idx else BG
                suffix = f" ✗"
            else:
                bg = BG2 if i != self.current_sprint_idx else ACCENT
                fg = FG if i != self.current_sprint_idx else BG
                suffix = f" {passed}/{total}"

            btn.configure(
                bg=ACCENT if i == self.current_sprint_idx else bg,
                fg=BG if i == self.current_sprint_idx else fg,
                text=SPRINTS[i]["label"] + suffix
            )

    def _update_overall_label(self):
        total_pass = sum(
            1 for s in SPRINTS for t in s["tests"]
            if self.results.get(t["id"], {}).get("status") == "pass"
        )
        total_tests = sum(len(s["tests"]) for s in SPRINTS)
        self.overall_label.configure(
            text=f"Overall: {total_pass}/{total_tests} tests passing"
        )

    def _show_saved_indicator(self):
        self.save_label.configure(text="● saved")
        self.root.after(2000, lambda: self.save_label.configure(text=""))

    # ── utilities ─────────────────────────────────────────────────────────────
    def _copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        self._show_saved_indicator()
        self.save_label.configure(text="● copied to clipboard")
        self.root.after(2500, lambda: self.save_label.configure(text=""))

    def _copy_failure_report(self):
        lines = [f"TradeIQ Validator Failure Report — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 "=" * 60]
        has_issues = False
        for sprint in SPRINTS:
            sprint_lines = []
            for test in sprint["tests"]:
                status = self.results.get(test["id"], {}).get("status", "pending")
                if status in ("fail", "pending"):
                    has_issues = True
                    out = self.results.get(test["id"], {}).get("output", "")
                    sprint_lines.append(
                        f"  [{status.upper()}] {test['name']}\n"
                        f"         Vector: {test['vector'][:80]}\n"
                        f"         Output: {out[:100] if out else 'none'}"
                    )
            if sprint_lines:
                lines.append(f"\n{sprint['label']}:")
                lines.extend(sprint_lines)

        if not has_issues:
            lines.append("\nAll tests passing! Nothing to report.")

        report = "\n".join(lines)
        self._copy_to_clipboard(report)

    def _reset_all(self):
        if messagebox.askyesno("Reset", "Reset all test results? This cannot be undone."):
            self.results = {}
            self._save_results()
            self._show_sprint(self.current_sprint_idx)
            self._update_sidebar_badges()
            self._update_overall_label()

    # ── Results Viewer ────────────────────────────────────────────────────────
    def _show_results_viewer(self):
        """Full Results Viewer panel — browse all sprint output files."""
        for w in self.content.winfo_children():
            w.destroy()

        # deselect all sprint buttons, highlight viewer btn
        for btn in self.sprint_btns:
            btn.configure(bg=BG2, fg=FG)
        self.results_viewer_btn.configure(bg=ACCENT, fg=BG)

        # ── outer layout: left file list + right viewer ───────────────────────
        pane = tk.Frame(self.content, bg=BG)
        pane.pack(fill="both", expand=True)

        # left file list (fixed width)
        file_list_frame = tk.Frame(pane, bg=BG2, width=250)
        file_list_frame.pack(side="left", fill="y")
        file_list_frame.pack_propagate(False)

        tk.Label(file_list_frame, text="OUTPUT FILES", bg=BG2, fg=FG2,
                 font=(SANS, 9, "bold")).pack(anchor="w", padx=12, pady=(14, 6))

        # search box
        search_var = tk.StringVar()
        search_entry = tk.Entry(file_list_frame, textvariable=search_var,
                                bg=BG3, fg=FG, insertbackground=FG,
                                font=(SANS, 9), relief="flat")
        search_entry.pack(fill="x", padx=8, pady=(0, 8), ipady=4)
        search_entry.insert(0, "Search files...")
        search_entry.bind("<FocusIn>",  lambda e: search_entry.delete(0, "end")
                          if search_entry.get() == "Search files..." else None)
        search_entry.bind("<FocusOut>", lambda e: search_entry.insert(0, "Search files...")
                          if not search_entry.get() else None)

        # file buttons container (scrollable)
        fl_canvas = tk.Canvas(file_list_frame, bg=BG2, highlightthickness=0)
        fl_sb = ttk.Scrollbar(file_list_frame, orient="vertical",
                              command=fl_canvas.yview)
        fl_canvas.configure(yscrollcommand=fl_sb.set)
        fl_sb.pack(side="right", fill="y")
        fl_canvas.pack(side="left", fill="both", expand=True)
        fl_inner = tk.Frame(fl_canvas, bg=BG2)
        fl_canvas.create_window((0, 0), window=fl_inner, anchor="nw")
        fl_inner.bind("<Configure>",
                      lambda e: fl_canvas.configure(scrollregion=fl_canvas.bbox("all")))

        # right viewer
        viewer_frame = tk.Frame(pane, bg=BG)
        viewer_frame.pack(side="left", fill="both", expand=True)

        # viewer top bar
        viewer_top = tk.Frame(viewer_frame, bg=BG2, height=40)
        viewer_top.pack(fill="x")
        viewer_top.pack_propagate(False)
        self._viewer_title = tk.Label(viewer_top, text="Select a file from the left panel",
                                       bg=BG2, fg=FG2, font=(SANS, 10))
        self._viewer_title.pack(side="left", padx=14, pady=10)
        self._viewer_info = tk.Label(viewer_top, text="", bg=BG2, fg=FG2,
                                      font=(SANS, 9))
        self._viewer_info.pack(side="right", padx=14)

        # viewer toolbar
        toolbar = tk.Frame(viewer_frame, bg=BG3, height=34)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        self._search_viewer_var = tk.StringVar()
        search_in_viewer = tk.Entry(toolbar, textvariable=self._search_viewer_var,
                                    bg=BG2, fg=FG, insertbackground=FG,
                                    font=(SANS, 9), relief="flat", width=24)
        search_in_viewer.pack(side="left", padx=8, pady=5, ipady=3)
        search_in_viewer.insert(0, "Search in output...")
        search_in_viewer.bind("<FocusIn>",
                              lambda e: search_in_viewer.delete(0, "end")
                              if search_in_viewer.get() == "Search in output..." else None)

        tk.Button(toolbar, text="Find",
                  bg=BTN_BG, fg=FG, font=(SANS, 9), relief="flat",
                  cursor="hand2", padx=6, pady=2,
                  command=lambda: self._find_in_viewer(viewer_text,
                                                        self._search_viewer_var.get())
                  ).pack(side="left", padx=(0, 8))

        tk.Button(toolbar, text="Copy All",
                  bg=BTN_BG, fg=FG, font=(SANS, 9), relief="flat",
                  cursor="hand2", padx=6, pady=2,
                  command=lambda: self._copy_to_clipboard(viewer_text.get("1.0", "end"))
                  ).pack(side="left", padx=(0, 4))

        tk.Button(toolbar, text="Refresh",
                  bg=BTN_BG, fg=GREEN, font=(SANS, 9), relief="flat",
                  cursor="hand2", padx=6, pady=2,
                  command=lambda: self._reload_current_file(viewer_text)
                  ).pack(side="left", padx=(0, 4))

        tk.Button(toolbar, text="Pretty Print JSON",
                  bg=BTN_BG, fg=BLUE, font=(SANS, 9), relief="flat",
                  cursor="hand2", padx=6, pady=2,
                  command=lambda: self._pretty_json(viewer_text)
                  ).pack(side="left", padx=(0, 4))

        # viewer text area
        viewer_text = scrolledtext.ScrolledText(
            viewer_frame, bg=BG3, fg=FG,
            font=(MONO, 10), relief="flat",
            wrap="none", insertbackground=FG,
            selectbackground=ACCENT, selectforeground=BG
        )
        viewer_text.pack(fill="both", expand=True, padx=0, pady=0)
        viewer_text.tag_configure("key",       foreground=BLUE)
        viewer_text.tag_configure("string",    foreground=GREEN)
        viewer_text.tag_configure("number",    foreground=AMBER)
        viewer_text.tag_configure("boolean",   foreground=ACCENT)
        viewer_text.tag_configure("highlight", background=AMBER, foreground=BG)
        viewer_text.tag_configure("section",   foreground=ACCENT, font=(MONO, 10, "bold"))
        viewer_text.tag_configure("good",      foreground=GREEN)
        viewer_text.tag_configure("bad",       foreground=RED)

        self._current_file_entry = None

        # ── build file list buttons ───────────────────────────────────────────
        file_btns = []

        def make_file_btn(entry):
            exists = self._file_exists(entry)
            fg_col = FG if exists else FG2
            dot_col = GREEN if exists else RED

            row = tk.Frame(fl_inner, bg=BG2, cursor="hand2")
            row.pack(fill="x", pady=1)

            dot = tk.Label(row, text="●", bg=BG2, fg=dot_col,
                           font=(SANS, 8))
            dot.pack(side="left", padx=(8, 4))

            lbl = tk.Label(row, text=entry["display"],
                           bg=BG2, fg=fg_col,
                           font=(SANS, 9), anchor="w", wraplength=180,
                           justify="left")
            lbl.pack(side="left", padx=(0, 4), pady=4)

            sub = tk.Label(row, text=entry["sprint"],
                           bg=BG2, fg=FG2, font=(SANS, 8))
            sub.pack(side="left", fill="x", expand=True)

            def on_click(e=entry, r=row, d=dot, l=lbl):
                for b in file_btns:
                    b.configure(bg=BG2)
                r.configure(bg=BG3)
                self._load_file_into_viewer(e, viewer_text)
                self._current_file_entry = e

            row.bind("<Button-1>",  lambda ev, fn=on_click: fn())
            dot.bind("<Button-1>",  lambda ev, fn=on_click: fn())
            lbl.bind("<Button-1>",  lambda ev, fn=on_click: fn())
            sub.bind("<Button-1>",  lambda ev, fn=on_click: fn())
            file_btns.append(row)
            return row, dot

        dot_refs = {}
        for entry in OUTPUT_FILES:
            row, dot = make_file_btn(entry)
            dot_refs[entry["label"]] = dot

        # ── company search + ticker picker ────────────────────────────────────
        tk.Frame(fl_inner, bg=BORDER, height=1).pack(fill="x", padx=8, pady=8)
        tk.Label(fl_inner, text="COMPANY SEARCH",
                 bg=BG2, fg=FG2, font=(SANS, 8, "bold")).pack(anchor="w", padx=12, pady=(0, 4))

        # selected company display badge
        self._selected_badge = tk.Label(
            fl_inner, text="Selected:  RELIANCE",
            bg=GREEN_BG, fg=GREEN,
            font=(SANS, 9, "bold"), anchor="w"
        )
        self._selected_badge.pack(fill="x", padx=8, pady=(0, 4), ipady=4, ipadx=8)

        # search input
        self._viewer_ticker = tk.StringVar(value="RELIANCE")
        self._search_company_var = tk.StringVar()
        search_co_entry = tk.Entry(
            fl_inner,
            textvariable=self._search_company_var,
            bg=BG3, fg=FG, insertbackground=FG,
            font=(SANS, 9), relief="flat"
        )
        search_co_entry.pack(fill="x", padx=8, pady=(0, 2), ipady=5)
        search_co_entry.insert(0, "Type company name or ticker...")

        def _clear_placeholder(e):
            if search_co_entry.get() == "Type company name or ticker...":
                search_co_entry.delete(0, "end")
                search_co_entry.configure(fg=FG)
        def _restore_placeholder(e):
            if not search_co_entry.get():
                search_co_entry.insert(0, "Type company name or ticker...")
                search_co_entry.configure(fg=FG2)
        search_co_entry.bind("<FocusIn>",  _clear_placeholder)
        search_co_entry.bind("<FocusOut>", _restore_placeholder)

        # dropdown listbox for results
        dropdown_frame = tk.Frame(fl_inner, bg=BG3)
        dropdown_frame.pack(fill="x", padx=8, pady=(0, 4))

        co_listbox = tk.Listbox(
            dropdown_frame,
            bg=BG3, fg=FG,
            selectbackground=ACCENT, selectforeground=BG,
            font=(SANS, 9),
            relief="flat",
            height=6,
            activestyle="none",
            borderwidth=0
        )
        co_listbox.pack(fill="x", side="left", expand=True)
        co_lb_sb = ttk.Scrollbar(dropdown_frame, orient="vertical",
                                  command=co_listbox.yview)
        co_listbox.configure(yscrollcommand=co_lb_sb.set)
        co_lb_sb.pack(side="right", fill="y")

        # sector filter
        sector_frame = tk.Frame(fl_inner, bg=BG2)
        sector_frame.pack(fill="x", padx=8, pady=(0, 2))
        tk.Label(sector_frame, text="Sector:", bg=BG2, fg=FG2,
                 font=(SANS, 8)).pack(side="left")
        self._sector_filter = tk.StringVar(value="All")
        sector_dd = ttk.Combobox(
            sector_frame,
            textvariable=self._sector_filter,
            values=["All", "Banking", "IT", "Energy", "Pharma", "Auto",
                    "FMCG", "Metals", "Telecom", "Infra", "Chemicals", "Realty"],
            font=(SANS, 8),
            width=14, state="readonly"
        )
        sector_dd.pack(side="left", padx=4)

        # recently viewed
        tk.Label(fl_inner, text="RECENTLY VIEWED",
                 bg=BG2, fg=FG2, font=(SANS, 8, "bold")).pack(
                     anchor="w", padx=12, pady=(6, 2))
        self._recent_frame = tk.Frame(fl_inner, bg=BG2)
        self._recent_frame.pack(fill="x", padx=8, pady=(0, 4))
        self._recent_tickers = []

        # ── populate listbox from NSE_COMPANIES ───────────────────────────────
        def _populate_listbox(query="", sector="All"):
            co_listbox.delete(0, "end")
            query = query.strip().lower()
            count = 0
            for ticker, info in NSE_COMPANIES.items():
                name   = info["name"].lower()
                sector_match = (sector == "All" or
                                info.get("sector", "").lower() == sector.lower())
                text_match   = (not query or
                                query in ticker.lower() or
                                query in name)
                if sector_match and text_match:
                    display = f"{ticker:<14} {info['name']}"
                    co_listbox.insert("end", display)
                    count += 1
                if count >= 80:
                    break
            if count == 0:
                co_listbox.insert("end", "  No matches found")

        _populate_listbox()

        def _on_search_type(event=None):
            q = self._search_company_var.get()
            if q == "Type company name or ticker...":
                q = ""
            _populate_listbox(q, self._sector_filter.get())

        def _on_sector_change(event=None):
            q = self._search_company_var.get()
            if q == "Type company name or ticker...":
                q = ""
            _populate_listbox(q, self._sector_filter.get())

        def _on_select(event=None):
            sel = co_listbox.curselection()
            if not sel:
                return
            item = co_listbox.get(sel[0])
            if "No matches" in item:
                return
            ticker = item.strip().split()[0]
            info   = NSE_COMPANIES.get(ticker, {})
            self._viewer_ticker.set(ticker)
            self._selected_badge.configure(
                text=f"Selected:  {ticker}  —  {info.get('name','')}")
            # add to recent
            if ticker not in self._recent_tickers:
                self._recent_tickers.insert(0, ticker)
                if len(self._recent_tickers) > 5:
                    self._recent_tickers.pop()
            _rebuild_recent()
            # auto reload
            if self._current_file_entry:
                self._reload_current_file(viewer_text)

        def _rebuild_recent():
            for w in self._recent_frame.winfo_children():
                w.destroy()
            for rt in self._recent_tickers:
                info = NSE_COMPANIES.get(rt, {})
                rb = tk.Button(
                    self._recent_frame,
                    text=rt,
                    bg=BTN_BG, fg=BLUE,
                    font=(SANS, 8), relief="flat",
                    cursor="hand2", padx=4, pady=1,
                    command=lambda t=rt, n=info.get("name",""): (
                        self._viewer_ticker.set(t),
                        self._selected_badge.configure(
                            text=f"Selected:  {t}  —  {n}"),
                        self._reload_current_file(viewer_text)
                    )
                )
                rb.pack(side="left", padx=2, pady=1)

        # keyboard navigation in listbox
        def _on_keypress(event):
            if event.keysym in ("Down",):
                co_listbox.focus_set()
                if co_listbox.size() > 0:
                    co_listbox.selection_set(0)
                    co_listbox.activate(0)
            elif event.keysym == "Return":
                _on_select()

        search_co_entry.bind("<KeyRelease>", _on_search_type)
        search_co_entry.bind("<Down>",       _on_keypress)
        search_co_entry.bind("<Return>",     _on_keypress)
        co_listbox.bind("<<ListboxSelect>>", _on_select)
        co_listbox.bind("<Return>",          _on_select)
        sector_dd.bind("<<ComboboxSelected>>", _on_sector_change)

        # date picker
        tk.Frame(fl_inner, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(6, 4))
        date_frame = tk.Frame(fl_inner, bg=BG2)
        date_frame.pack(fill="x", padx=8, pady=2)
        tk.Label(date_frame, text="Date:", bg=BG2, fg=FG2,
                 font=(SANS, 9)).pack(side="left")
        self._viewer_date = tk.StringVar(
            value=datetime.datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(date_frame, textvariable=self._viewer_date,
                 bg=BG3, fg=FG, insertbackground=FG,
                 font=(SANS, 9), relief="flat", width=12).pack(side="left", padx=4)

        # quick date buttons
        qd_frame = tk.Frame(fl_inner, bg=BG2)
        qd_frame.pack(fill="x", padx=8, pady=(0, 2))
        for label, delta in [("Today", 0), ("Yesterday", -1), ("Mon", None)]:
            def set_date(d=delta, l=label):
                if l == "Mon":
                    today = datetime.date.today()
                    days_back = (today.weekday() - 0) % 7
                    target = today - datetime.timedelta(days=days_back)
                else:
                    target = datetime.date.today() + datetime.timedelta(days=d)
                self._viewer_date.set(target.strftime("%Y-%m-%d"))
                if self._current_file_entry:
                    self._reload_current_file(viewer_text)
            tk.Button(qd_frame, text=label,
                      bg=BTN_BG, fg=FG2, font=(SANS, 8), relief="flat",
                      cursor="hand2", padx=6, pady=1,
                      command=set_date).pack(side="left", padx=2)

        tk.Button(fl_inner, text="Load Results for Selected Company",
                  bg=ACCENT, fg=BG, font=(SANS, 9, "bold"), relief="flat",
                  cursor="hand2", padx=6, pady=4,
                  command=lambda: self._reload_current_file(viewer_text)
                  ).pack(fill="x", padx=8, pady=(6, 2))

        # ── live file watcher ─────────────────────────────────────────────────
        tk.Frame(fl_inner, bg=BORDER, height=1).pack(fill="x", padx=8, pady=8)
        tk.Label(fl_inner, text="LIVE WATCH",
                 bg=BG2, fg=FG2, font=(SANS, 8, "bold")).pack(anchor="w", padx=12)

        self._watch_active = False
        self._watch_btn = tk.Button(
            fl_inner,
            text="Start Auto-Refresh (5s)",
            bg=BTN_BG, fg=GREEN, font=(SANS, 9), relief="flat",
            cursor="hand2", padx=6, pady=3,
            command=lambda: self._toggle_watch(viewer_text)
        )
        self._watch_btn.pack(fill="x", padx=8, pady=2)

        self._watch_status = tk.Label(fl_inner, text="", bg=BG2, fg=FG2,
                                       font=(SANS, 8))
        self._watch_status.pack(anchor="w", padx=12)

        # welcome message
        self._show_viewer_welcome(viewer_text)

    def _file_exists(self, entry):
        if entry.get("path"):
            return os.path.exists(entry["path"])
        if entry.get("path_template"):
            ticker = self._viewer_ticker.get() if hasattr(self, "_viewer_ticker") else "RELIANCE"
            date   = self._viewer_date.get()   if hasattr(self, "_viewer_date")   else datetime.datetime.now().strftime("%Y-%m-%d")
            p = entry["path_template"].replace("{ticker}", ticker.upper()).replace("{date}", date)
            return os.path.exists(p)
        return entry.get("cmd") is not None

    def _resolve_path(self, entry):
        if entry.get("path"):
            return entry["path"]
        if entry.get("path_template"):
            ticker = self._viewer_ticker.get().upper()
            date   = self._viewer_date.get()
            return entry["path_template"].replace("{ticker}", ticker).replace("{date}", date)
        return None

    def _load_file_into_viewer(self, entry, text_widget):
        self._current_file_entry = entry
        self._viewer_title.configure(text=entry["display"])
        self._viewer_info.configure(text=entry["desc"])
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")

        # run command if needed
        if entry.get("cmd"):
            text_widget.insert("end", "Running command...\n\n", "section")
            self.root.update()

            def _run_cmd():
                try:
                    proc = subprocess.run(entry["cmd"], capture_output=True,
                                          text=True, timeout=30)
                    raw = proc.stdout.strip() or proc.stderr.strip() or "(no output)"
                    self.root.after(0, lambda: self._display_output(text_widget, raw, entry["format"]))
                except Exception as e:
                    self.root.after(0, lambda: self._display_output(
                        text_widget, f"Error: {e}", "text"))
            threading.Thread(target=_run_cmd, daemon=True).start()
            return

        # read file
        path = self._resolve_path(entry)
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    raw = f.read()
                size = os.path.getsize(path)
                mtime = datetime.datetime.fromtimestamp(
                    os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
                self._viewer_info.configure(
                    text=f"{entry['desc']}   |   {size:,} bytes   |   Modified: {mtime}")
                self._display_output(text_widget, raw, entry["format"])
            except Exception as e:
                text_widget.insert("end", f"Error reading file:\n{e}", "bad")
        else:
            self._show_file_not_found(text_widget, path, entry)

        text_widget.configure(state="disabled")

    def _display_output(self, text_widget, raw, fmt):
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")

        if fmt == "json":
            try:
                data = json.loads(raw)
                self._render_json(text_widget, data)
                return
            except json.JSONDecodeError:
                pass

        # plain text with smart colouring
        for line in raw.splitlines():
            line_stripped = line.strip().lower()
            if any(k in line_stripped for k in ("error", "fail", "exception", "traceback")):
                text_widget.insert("end", line + "\n", "bad")
            elif any(k in line_stripped for k in ("ok", "pass", "success", "complete")):
                text_widget.insert("end", line + "\n", "good")
            elif line_stripped.startswith(("#", "//", "=", "-")):
                text_widget.insert("end", line + "\n", "section")
            else:
                text_widget.insert("end", line + "\n")
        text_widget.configure(state="disabled")

    def _render_json(self, text_widget, data, indent=0, is_last=True):
        """Recursively render JSON with syntax colouring."""
        pad = "  " * indent

        def ins(text, tag=""):
            text_widget.insert("end", text, tag)

        if isinstance(data, dict):
            ins("{\n")
            items = list(data.items())
            for i, (k, v) in enumerate(items):
                comma = "" if i == len(items) - 1 else ","
                ins(pad + "  ")
                ins(f'"{k}"', "key")
                ins(": ")
                self._render_json_value(text_widget, v, indent + 1,
                                        i == len(items) - 1)
                ins(comma + "\n")
            ins(pad + "}")
        elif isinstance(data, list):
            ins("[\n")
            for i, item in enumerate(data):
                comma = "" if i == len(data) - 1 else ","
                ins(pad + "  ")
                self._render_json_value(text_widget, item, indent + 1,
                                        i == len(data) - 1)
                ins(comma + "\n")
            ins(pad + "]")
        else:
            self._render_json_value(text_widget, data, indent, is_last)
        text_widget.configure(state="disabled")

    def _render_json_value(self, tw, val, indent, is_last):
        pad = "  " * indent

        def ins(text, tag=""):
            tw.insert("end", text, tag)

        if isinstance(val, dict):
            ins("{\n")
            items = list(val.items())
            for i, (k, v) in enumerate(items):
                comma = "" if i == len(items) - 1 else ","
                ins(pad + "  ")
                ins(f'"{k}"', "key")
                ins(": ")
                self._render_json_value(tw, v, indent + 1, i == len(items) - 1)
                ins(comma + "\n")
            ins(pad + "}")
        elif isinstance(val, list):
            if not val:
                ins("[]")
            elif all(isinstance(x, (str, int, float, bool)) for x in val):
                # compact single-line array for simple types
                ins("[")
                for i, x in enumerate(val):
                    self._render_json_value(tw, x, indent, i == len(val) - 1)
                    if i < len(val) - 1:
                        ins(", ")
                ins("]")
            else:
                ins("[\n")
                for i, item in enumerate(val):
                    comma = "" if i == len(val) - 1 else ","
                    ins(pad + "  ")
                    self._render_json_value(tw, item, indent + 1,
                                            i == len(val) - 1)
                    ins(comma + "\n")
                ins(pad + "]")
        elif isinstance(val, bool):
            ins(str(val).lower(), "boolean")
        elif isinstance(val, (int, float)):
            ins(str(val), "number")
        elif val is None:
            ins("null", "boolean")
        else:
            # string — colour-code known value patterns
            s = str(val)
            tag = "string"
            sl = s.lower()
            if sl in ("strongly_positive", "positive", "trending_bull",
                      "long", "net_buyer", "raised", "pass", "win", "ok"):
                tag = "good"
            elif sl in ("negative", "strongly_negative", "trending_bear",
                        "do_not_trade", "short", "net_seller", "cut",
                        "fail", "loss", "error"):
                tag = "bad"
            ins(f'"{s}"', tag)

    def _show_file_not_found(self, tw, path, entry):
        tw.configure(state="normal")
        tw.delete("1.0", "end")
        tw.insert("end", "File not found\n\n", "bad")
        tw.insert("end", f"Expected path:\n  {path or '(dynamic)'}\n\n", "section")
        tw.insert("end", "This file is generated when the corresponding sprint layer runs.\n", "")
        tw.insert("end", "To generate it:\n", "section")

        if entry.get("path_template") and "{ticker}" in entry.get("path_template", ""):
            tw.insert("end", f"  1. Set ticker to your desired company above\n", "")
            tw.insert("end", f"  2. Run: python backend/layers/layer1_news.py --ticker {self._viewer_ticker.get().upper()}\n", "key")
        elif entry.get("path_template") and "{date}" in entry.get("path_template", ""):
            tw.insert("end", f"  1. Set date to today above\n", "")
            tw.insert("end", f"  2. Run the Layer 2 scoring pipeline\n", "key")
        else:
            tw.insert("end", f"  Run the pipeline for {entry['sprint']}\n", "key")

        tw.insert("end", "\nOnce generated, click Refresh to load it here.\n", "")
        tw.configure(state="disabled")

    def _show_viewer_welcome(self, tw):
        tw.configure(state="normal")
        tw.delete("1.0", "end")
        tw.insert("end", "TradeIQ Results Viewer\n", "section")
        tw.insert("end", "─" * 50 + "\n\n", "section")
        tw.insert("end", "This panel shows the actual output your TradeIQ\n")
        tw.insert("end", "intelligence layers are producing.\n\n")
        tw.insert("end", "Click any file on the left to view it.\n\n")
        tw.insert("end", "What each file tells you:\n", "section")
        for entry in OUTPUT_FILES:
            exists = self._file_exists(entry)
            dot = "●" if exists else "○"
            col = "good" if exists else "bad"
            tw.insert("end", f"  {dot} ", col)
            tw.insert("end", f"{entry['display']}\n", "key")
            tw.insert("end", f"     {entry['desc']}\n", "")
        tw.insert("end", "\n")
        tw.insert("end", "● = file exists on disk\n", "good")
        tw.insert("end", "○ = not generated yet (run the sprint first)\n", "bad")
        tw.configure(state="disabled")

    def _find_in_viewer(self, tw, search_term):
        if not search_term or search_term == "Search in output...":
            return
        tw.tag_remove("highlight", "1.0", "end")
        start = "1.0"
        count = 0
        while True:
            pos = tw.search(search_term, start, stopindex="end",
                            nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(search_term)}c"
            tw.tag_add("highlight", pos, end_pos)
            start = end_pos
            count += 1
        if count:
            first = tw.tag_ranges("highlight")
            if first:
                tw.see(first[0])
            self._viewer_info.configure(text=f"{count} match(es) found for '{search_term}'")
        else:
            self._viewer_info.configure(text=f"No matches for '{search_term}'")

    def _pretty_json(self, tw):
        tw.configure(state="normal")
        raw = tw.get("1.0", "end").strip()
        try:
            data = json.loads(raw)
            tw.delete("1.0", "end")
            self._render_json(tw, data)
        except Exception:
            self._viewer_info.configure(text="Content is not valid JSON")
        tw.configure(state="disabled")

    def _reload_current_file(self, tw):
        if self._current_file_entry:
            self._load_file_into_viewer(self._current_file_entry, tw)
        else:
            self._show_viewer_welcome(tw)

    def _toggle_watch(self, tw):
        self._watch_active = not self._watch_active
        if self._watch_active:
            self._watch_btn.configure(text="Stop Auto-Refresh", fg=RED)
            self._watch_loop(tw)
        else:
            self._watch_btn.configure(text="Start Auto-Refresh (5s)", fg=GREEN)
            self._watch_status.configure(text="")

    def _watch_loop(self, tw):
        if not self._watch_active:
            return
        if self._current_file_entry:
            self._reload_current_file(tw)
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self._watch_status.configure(text=f"Last refresh: {now}")
        self.root.after(5000, lambda: self._watch_loop(tw))
if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap("")
    except Exception:
        pass

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Vertical.TScrollbar",
                     background=BG3, troughcolor=BG2,
                     arrowcolor=FG2, bordercolor=BG2)

    app = TradeIQValidator(root)
    root.mainloop()
