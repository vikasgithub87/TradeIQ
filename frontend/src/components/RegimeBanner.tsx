/**
 * RegimeBanner.tsx — Live market regime status banner
 * Shown at the top of every dashboard page.
 * Fetches from GET /regime/today on the FastAPI backend.
 */
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string

interface RegimeData {
  date:                     string
  regime:                   string
  regime_score:             number
  do_not_trade:             boolean
  india_vix:                number | null
  crude_oil_usd:            number | null
  sp500_futures:            { change_pct: number; direction: string } | null
  is_expiry_day:            boolean
  is_monthly_expiry?:       boolean
  is_weekly_expiry?:        boolean
  is_rbi_day:               boolean
  is_budget_day:            boolean
  signal_threshold_l2:      number
  position_size_multiplier: number
  allowed_directions:       string[]
  regime_reason:            string
  warning?:                 string
}

const REGIME_STYLES: Record<string, {
  bg: string; border: string; text: string; badge: string; icon: string
}> = {
  TRENDING_BULL:   { bg: "#f0fdf4", border: "#86efac", text: "#14532d", badge: "#16a34a", icon: "▲" },
  TRENDING_BEAR:   { bg: "#fff7ed", border: "#fed7aa", text: "#7c2d12", badge: "#ea580c", icon: "▼" },
  RANGE_BOUND:     { bg: "#f0f9ff", border: "#bae6fd", text: "#0c4a6e", badge: "#0284c7", icon: "─" },
  HIGH_VOLATILITY: { bg: "#fefce8", border: "#fde047", text: "#713f12", badge: "#ca8a04", icon: "⚡" },
  EXPIRY_CAUTION:  { bg: "#fefce8", border: "#fde047", text: "#713f12", badge: "#ca8a04", icon: "⚠" },
  DO_NOT_TRADE:    { bg: "#fef2f2", border: "#fca5a5", text: "#7f1d1d", badge: "#dc2626", icon: "✗" },
  MARKET_CLOSED:   { bg: "#f9fafb", border: "#e5e7eb", text: "#374151", badge: "#6b7280", icon: "—" },
}

const DEFAULT_STYLE = {
  bg: "#f9fafb", border: "#e5e7eb", text: "#374151", badge: "#6b7280", icon: "?"
}

export default function RegimeBanner() {
  const [regime,  setRegime]  = useState<RegimeData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    if (!API_URL || API_URL === "undefined") {
      setError("API URL not configured")
      setLoading(false)
      return
    }
    axios.get(`${API_URL}/regime/today`)
      .then(res => { setRegime(res.data); setLoading(false) })
      .catch(err => {
        if (err.response?.status === 404) {
          setError("Regime not generated yet - run layer0.py first")
        } else {
          setError("Cannot reach backend")
        }
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div style={{ padding: "10px 16px", background: "#f9fafb",
                    borderRadius: 8, marginBottom: 20,
                    fontSize: 13, color: "#6b7280" }}>
        Loading market regime...
      </div>
    )
  }

  if (error || !regime) {
    return (
      <div style={{ padding: "10px 16px", background: "#fef2f2",
                    border: "1px solid #fca5a5", borderRadius: 8,
                    marginBottom: 20, fontSize: 13, color: "#991b1b" }}>
        {error || "Regime unavailable"}
      </div>
    )
  }

  const style = REGIME_STYLES[regime.regime] || DEFAULT_STYLE

  return (
    <div style={{ background: style.bg, border: `1px solid ${style.border}`,
                  borderRadius: 10, padding: "14px 18px",
                  marginBottom: 24, color: style.text }}>

      {/* Top row */}
      <div style={{ display: "flex", alignItems: "center",
                    justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ background: style.badge, color: "#fff",
                          fontSize: 12, fontWeight: 600,
                          padding: "3px 10px", borderRadius: 20 }}>
            {style.icon} {regime.regime.replace(/_/g, " ")}
          </span>
          <span style={{ fontSize: 13, fontWeight: 500 }}>
            {regime.regime_reason}
          </span>
        </div>
        <div style={{ display: "flex", gap: 16, fontSize: 12 }}>
          {regime.india_vix !== null && (
            <span>VIX <strong>{regime.india_vix}</strong></span>
          )}
          {regime.crude_oil_usd && (
            <span>Crude <strong>${regime.crude_oil_usd}</strong></span>
          )}
          {regime.sp500_futures && (
            <span>S&P500 <strong style={{
              color: regime.sp500_futures.change_pct >= 0 ? "#16a34a" : "#dc2626"
            }}>
              {regime.sp500_futures.change_pct >= 0 ? "+" : ""}
              {regime.sp500_futures.change_pct.toFixed(2)}%
            </strong></span>
          )}
        </div>
      </div>

      {/* Flags row */}
      {(regime.is_expiry_day || regime.is_rbi_day || regime.is_budget_day) && (
        <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {regime.is_monthly_expiry && (
            <span style={{ fontSize: 11, padding: "2px 8px",
                            background: style.badge, color: "#fff",
                            borderRadius: 10 }}>Monthly Expiry</span>
          )}
          {regime.is_weekly_expiry && !regime.is_monthly_expiry && (
            <span style={{ fontSize: 11, padding: "2px 8px",
                            background: style.badge, color: "#fff",
                            borderRadius: 10 }}>Weekly Expiry</span>
          )}
          {regime.is_rbi_day && (
            <span style={{ fontSize: 11, padding: "2px 8px",
                            background: "#7c3aed", color: "#fff",
                            borderRadius: 10 }}>RBI Policy Day</span>
          )}
          {regime.is_budget_day && (
            <span style={{ fontSize: 11, padding: "2px 8px",
                            background: "#dc2626", color: "#fff",
                            borderRadius: 10 }}>Union Budget Day</span>
          )}
        </div>
      )}

      {/* Trading parameters — only if market is open and trading allowed */}
      {!regime.do_not_trade && (
        <div style={{ marginTop: 10, paddingTop: 10,
                      borderTop: `1px solid ${style.border}`,
                      display: "flex", gap: 20, flexWrap: "wrap", fontSize: 12 }}>
          <span>L2 threshold: <strong>≥{regime.signal_threshold_l2}</strong></span>
          <span>Position size: <strong>
            {Math.round(regime.position_size_multiplier * 100)}%
          </strong></span>
          <span>Directions: <strong>
            {regime.allowed_directions.join(", ") || "None"}
          </strong></span>
          <span>Score: <strong>{regime.regime_score}/100</strong></span>
        </div>
      )}

      {/* Do not trade warning */}
      {regime.do_not_trade && (
        <div style={{ marginTop: 10, fontSize: 13, fontWeight: 600 }}>
          ⚠ No trade signals will be generated today. Stay out.
        </div>
      )}

      {/* Stale data warning */}
      {regime.warning && (
        <div style={{ marginTop: 8, fontSize: 12, color: "#92400e" }}>
          ⚠ {regime.warning}
        </div>
      )}
    </div>
  )
}
