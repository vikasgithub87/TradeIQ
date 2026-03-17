# TradeIQ — Commands Executed

## 1. Generate regime data
```
cd c:\Users\m3n2c7\TradeIQ
python backend\layers\layer0.py --date 2025-03-17 --mock-vix 14.0
```
**Result:** Regime RANGE_BOUND saved to `backend/data/regime_context.json`

---

## 2. Start backend (background)
```
cd c:\Users\m3n2c7\TradeIQ
python -m uvicorn backend.main:app --reload --port 8000
```
**Result:** Backend running at http://localhost:8000

---

## 3. Start frontend (background)
```
cd c:\Users\m3n2c7\TradeIQ\frontend
npm run dev
```
**Result:** Frontend running at http://localhost:5173

---

## 4. Verify backend health
```
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```
**Result:** `{"status":"ok","db":"disconnected","version":"1.0","sprint":"1"}`

---

## 5. Verify regime API
```
Invoke-WebRequest -Uri http://localhost:8000/regime/today -UseBasicParsing
```
**Result:** Regime JSON returned successfully

---

## 6. Run validation tests
```
python -c "import sys; sys.path.insert(0,'.'); from backend.layers.layer0 import classify_regime; ..."
```
**Result:** s2_2 ok, s2_3 ok, s2_4 ok

---

## 7. Generate regime for today
```
python backend\layers\layer0.py
```
**Result:** Regime for 2026-03-17 (TRENDING BEAR) saved

---

## OPEN NOW
**http://localhost:5173**

Login with your Supabase account to see the dashboard and regime banner.
