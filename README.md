# TradeIQ

AI-powered intraday trading intelligence platform for NSE India.

## Proof of Concept

Runs sentiment analysis on NSE companies using live news + Claude API.

### POC Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in API keys.
3. Run: `python poc_script.py`

For each of 3 companies (RELIANCE, INFY, HDFCBANK) you get news + a 3-sentence analyst brief.

---

## Sprint 1 — Foundation

FastAPI backend, React + TypeScript frontend, Supabase (PostgreSQL + Auth).

### Prerequisites

- Python 3.10+ (3.11 or 3.12 recommended; 3.14 may need `psycopg2-binary` workaround on Windows)
- Node.js 18+
- Supabase project with `DATABASE_URL` in `.env`

### Backend

1. Install backend deps (from project root):
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Ensure `.env` has: `ANTHROPIC_API_KEY`, `NEWSAPI_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `DATABASE_URL`.
3. Start API (from project root):
   ```bash
   py -m uvicorn backend.main:app --reload --port 8000
   ```
   If `uvicorn` is on PATH you can use: `uvicorn backend.main:app --reload --port 8000`
4. Tables are created on startup. Validate with: `python database_check.py`.

### Frontend

1. Create frontend (if not present):
   ```bash
   npm create vite@latest frontend -- --template react-ts
   ```
2. Install deps (from project root). Use the same command you use for Node:
   ```bash
   cd frontend
   npm install
   npm install @supabase/supabase-js axios react-router-dom
   npm install -D @types/node
   cd ..
   ```
   If `npm` is not recognized, open a **new** terminal (or restart) after installing Node.js, or use the full path to npm (e.g. `"C:\Program Files\nodejs\npm.cmd" install`).
3. Copy env for frontend (from project root):
   ```bash
   copy .env frontend\.env.local
   ```
   Then edit `frontend/.env.local`: keep only these and use your real values:
   - `VITE_SUPABASE_URL=<your SUPABASE_URL>`
   - `VITE_SUPABASE_ANON_KEY=<your SUPABASE_ANON_KEY>`
   - `VITE_API_URL=http://localhost:8000`
4. Start dev server:
   ```bash
   cd frontend
   npm run dev
   ```

### Run Sprint 1

- **Terminal 1 — Backend** (from project root):
  ```bash
  py -m uvicorn backend.main:app --reload --port 8000
  ```
- **Terminal 2 — Frontend:**
  ```bash
  cd frontend
  npm run dev
  ```
  If `npm` is not recognized, use a terminal where Node.js is on PATH (e.g. "Node.js command prompt") or add Node’s folder to your PATH.

Open http://localhost:5173 — register/login with Supabase Auth, then see the dashboard with API and DB status.
