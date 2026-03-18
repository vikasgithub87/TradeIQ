/**
 * ScoresPanel.tsx — Live BUY scores leaderboard.
 */
import { useEffect, useState } from 'react'
import axios from 'axios'
import ShortSignalCard, { type ShortScore } from './ShortSignalCard'
import TechnicalCard from './TechnicalCard'

const API_URL = import.meta.env.VITE_API_URL as string

interface ScoreEntry {
  ticker:           string
  buy_score:        number
  signal:           string
  short_score?:     number
  short_signal?:    string
  top_factors:      string[]
  velocity_label:   string
  score_delta:      number
  is_breakout:      boolean
  streak_days:      number
  sector:           string
  catalyst_summary: string
  flags:            string[]
  score_breakdown:  Record<string, number>
}

interface ScoresData {
  date:            string
  regime:          string
  threshold:       number
  total_companies: number
  above_threshold: number
  top_scores:      ScoreEntry[]
  short_scores:    ScoreEntry[]
  rotation_alerts: Array<{ sector: string; message: string; strength: string }>
  breakout_stocks: ScoreEntry[]
}

const SIGNAL_COLORS: Record<string, { bg: string; text: string }> = {
  strong_buy:   { bg: "#dcfce7", text: "#15803d" },
  buy:          { bg: "#d1fae5", text: "#065f46" },
  moderate_buy: { bg: "#fef9c3", text: "#854d0e" },
  watch:        { bg: "#f3f4f6", text: "#374151" },
  avoid:        { bg: "#fee2e2", text: "#991b1b" },
}

const VELOCITY_COLORS: Record<string, string> = {
  surging:      "#15803d",
  rising_fast:  "#16a34a",
  rising:       "#4ade80",
  stable:       "#6b7280",
  falling:      "#f97316",
  dropping:     "#dc2626",
}

export default function ScoresPanel() {
  const [data,    setData]    = useState<ScoresData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [thresholdInput, setThresholdInput] = useState('60')
  const [l3Signals, setL3Signals] = useState<Record<string, number>>({})
  const [sortBy, setSortBy] = useState<string>(
    () => localStorage.getItem('tradeiq_sort') || 'score_desc'
  )
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [shortData, setShortData] = useState<ShortScore[]>([])
  const [l3Running, setL3Running] = useState(false)

  const fetchScores = () => {
    setLoading(true)
    setError(null)
    if (!API_URL || API_URL === 'undefined') {
      setError('API URL not configured')
      setLoading(false)
      return
    }
    axios.get(`${API_URL}/scores/today?limit=10`)
      .then(res => {
        setData(res.data)
        const raw = (res.data.short_scores || []) as Record<string, unknown>[]
        setShortData(
          raw.map((s) => ({
            ticker: String(s.ticker ?? ''),
            short_score: Number(s.short_score ?? 0),
            short_signal: String(s.short_signal ?? 'no_short'),
            short_breakdown: (s.short_breakdown as Record<string, number>) || {},
            short_top_factors: (s.short_top_factors as string[]) || [],
            short_flags: (s.short_flags as string[]) || [],
            sector: String(s.sector ?? ''),
            score_delta: Number(s.score_delta ?? 0),
            velocity_label: String(s.velocity_label ?? 'stable'),
            is_breakout: Boolean(s.is_breakout),
            streak_days: Number(s.streak_days ?? 0),
            catalyst_summary: String(s.catalyst_summary ?? ''),
            recommended_direction: s.recommended_direction != null
              ? String(s.recommended_direction)
              : undefined,
            direction_reason: s.direction_reason != null
              ? String(s.direction_reason)
              : undefined,
            l3_flags: (s.l3_flags as string[]) || (s.flags as string[]) || [],
          }))
        )
        setLoading(false)
      })
      .catch(err => {
        setError(
          err.response?.status === 404
            ? 'Scores not generated yet. Run Layer 2 first.'
            : 'Cannot reach backend'
        )
        setLoading(false)
      })

    // Fetch L3 confidence scores for sorting
    axios.get(`${API_URL}/signals/today?limit=50`)
      .then(res => {
        const map: Record<string, number> = {}
        const allSigs = res.data.all_signals || []
        allSigs.forEach((s: any) => {
          map[s.ticker] = s.confidence_score || 0
        })
        setL3Signals(map)
      })
      .catch(() => {})
  }

  useEffect(() => { fetchScores() }, [])

  const parseThreshold = () => {
    const n = parseInt(thresholdInput, 10)
    if (Number.isNaN(n)) return undefined
    return Math.max(0, Math.min(100, n))
  }

  const runScores = () => {
    setLoading(true)
    setSuccessMsg(null)
    const th = parseThreshold()
    const qs = th != null ? `?threshold=${th}` : ''
    axios.post<{ message?: string; threshold?: number }>(`${API_URL}/scores/run${qs}`)
      .then((res) => {
        const t = res.data.threshold ?? th
        setSuccessMsg(
          t != null
            ? `Scoring successful — threshold ${t}.`
            : (res.data.message ?? 'Scoring successful.')
        )
        fetchScores()
      })
      .catch((err) => {
        setLoading(false)
        const d = err.response?.data?.detail
        setError(typeof d === 'string' ? d : 'Failed to run scoring')
      })
  }

  const runScoresOverride = () => {
    setLoading(true)
    setError(null)
    setSuccessMsg(null)
    const th = parseThreshold()
    const qs = new URLSearchParams()
    qs.set('ignore_regime', 'true')
    if (th != null) qs.set('threshold', String(th))
    axios.post<{ message?: string; threshold?: number }>(
      `${API_URL}/scores/run?${qs.toString()}`
    )
      .then((res) => {
        const t = res.data.threshold ?? th ?? 60
        setSuccessMsg(
          res.data.message
            ?? `Override successful — regime ignored, scoring ran with threshold ${t}.`
        )
        fetchScores()
      })
      .catch((err) => {
        setLoading(false)
        const d = err.response?.data?.detail
        setError(typeof d === 'string' ? d : 'Failed to run scoring (override)')
      })
  }

  const runLayer3 = () => {
    setL3Running(true)
    setError(null)
    setSuccessMsg(null)
    axios.post<{ total_validated?: number; buy_signals?: number; short_signals?: number }>(
      `${API_URL}/signals/run`
    )
      .then((res) => {
        const tv = res.data.total_validated ?? 0
        const b = res.data.buy_signals ?? 0
        const s = res.data.short_signals ?? 0
        setSuccessMsg(`Layer 3 complete — validated ${tv} (BUY ${b}, SHORT ${s}).`)
        setL3Running(false)
      })
      .catch((err) => {
        const d = err.response?.data?.detail
        setError(typeof d === 'string' ? d : 'Failed to run Layer 3')
        setL3Running(false)
      })
  }

  const sortedScores = [...(data?.top_scores || [])].sort((a, b) => {
    switch (sortBy) {
      case 'confidence_desc':
        return (l3Signals[b.ticker] || 0) - (l3Signals[a.ticker] || 0)
      case 'confidence_asc':
        return (l3Signals[a.ticker] || 0) - (l3Signals[b.ticker] || 0)
      case 'score_desc':
        return (b.buy_score || 0) - (a.buy_score || 0)
      case 'score_asc':
        return (a.buy_score || 0) - (b.buy_score || 0)
      case 'rr_desc': {
        // L3 R:R not in scores — sort by score as proxy if L3 unavailable
        const rr_b = l3Signals[b.ticker] ? l3Signals[b.ticker] : b.buy_score || 0
        const rr_a = l3Signals[a.ticker] ? l3Signals[a.ticker] : a.buy_score || 0
        return rr_b - rr_a
      }
      case 'move_desc':
        return (b.buy_score || 0) - (a.buy_score || 0) // proxy until L3 loaded
      case 'volume_desc':
        return (b.velocity_label === 'surging' ? 1 : 0) - (a.velocity_label === 'surging' ? 1 : 0)
      case 'velocity_desc': {
        const velOrder: Record<string, number> = {
          surging: 6, rising_fast: 5, rising: 4,
          stable: 3, falling: 2, dropping: 1,
        }
        return (velOrder[b.velocity_label] || 0) - (velOrder[a.velocity_label] || 0)
      }
      case 'streak_desc':
        return (b.streak_days || 0) - (a.streak_days || 0)
      case 'rsi_neutral': {
        // Sort by RSI distance from 50 — closest = least risky
        const rsi_a = l3Signals[a.ticker] || 50
        const rsi_b = l3Signals[b.ticker] || 50
        return Math.abs(rsi_a - 50) - Math.abs(rsi_b - 50)
      }
      case 'alpha':
        return (a.ticker || '').localeCompare(b.ticker || '')
      default:
        return (b.buy_score || 0) - (a.buy_score || 0)
    }
  })

  const sortedShorts = [...shortData].sort((a, b) => {
    switch (sortBy) {
      case 'confidence_desc':
        return (l3Signals[b.ticker] || 0) - (l3Signals[a.ticker] || 0)
      case 'confidence_asc':
        return (l3Signals[a.ticker] || 0) - (l3Signals[b.ticker] || 0)
      case 'velocity_desc': {
        const velOrder: Record<string, number> = {
          surging: 6, rising_fast: 5, rising: 4,
          stable: 3, falling: 2, dropping: 1,
        }
        return (velOrder[b.velocity_label] || 0) - (velOrder[a.velocity_label] || 0)
      }
      case 'streak_desc':
        return (b.streak_days || 0) - (a.streak_days || 0)
      case 'alpha':
        return (a.ticker || '').localeCompare(b.ticker || '')
      default:
        return (b.short_score || 0) - (a.short_score || 0)
    }
  })

  if (loading) {
    return (
      <div style={{ padding: 16, fontSize: 13, color: '#6b7280' }}>
        Loading scores...
      </div>
    )
  }

  return (
    <div style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>
            Today's BUY Signals
          </h2>
          {data && (
            <p style={{ fontSize: 12, color: '#6b7280', margin: '4px 0 0' }}>
              {data.above_threshold} companies above
              threshold {data.threshold} · Regime: {data.regime}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {/* Sort controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label style={{ fontSize: 12, color: '#6b7280', whiteSpace: 'nowrap' }}>
              Sort by:
            </label>
            <select
              value={sortBy}
              onChange={e => {
                setSortBy(e.target.value)
                localStorage.setItem('tradeiq_sort', e.target.value)
              }}
              style={{
                fontSize: 12,
                padding: '5px 8px',
                border: '1px solid #e5e7eb',
                borderRadius: 6,
                background: '#fff',
                color: '#374151',
                cursor: 'pointer',
              }}
            >
              <optgroup label="Confidence (Layer 3)">
                <option value="confidence_desc">Confidence: High → Low</option>
                <option value="confidence_asc">Confidence: Low → High</option>
              </optgroup>
              <optgroup label="Score (Layer 2)">
                <option value="score_desc">L2 Score: High → Low</option>
                <option value="score_asc">L2 Score: Low → High</option>
              </optgroup>
              <optgroup label="Trade quality">
                <option value="rr_desc">R:R Ratio: Best first</option>
                <option value="move_desc">Expected Move %: Highest first</option>
              </optgroup>
              <optgroup label="Market activity">
                <option value="volume_desc">Volume: Highest first</option>
                <option value="velocity_desc">Velocity: Surging first</option>
                <option value="streak_desc">Streak: Longest first</option>
              </optgroup>
              <optgroup label="Technical">
                <option value="rsi_neutral">RSI: Closest to 50</option>
              </optgroup>
              <optgroup label="Other">
                <option value="alpha">Alphabetical A → Z</option>
              </optgroup>
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: 11, color: '#6b7280' }}>Threshold</span>
            <input
              type="number"
              min={0}
              max={100}
              value={thresholdInput}
              onChange={e => setThresholdInput(e.target.value)}
              style={{
                width: 64,
                padding: '4px 6px',
                fontSize: 11,
                borderRadius: 4,
                border: '1px solid #e5e7eb',
              }}
            />
          </div>
          <button onClick={runScores}
            style={{ padding: '8px 14px', fontSize: 13,
                     background: '#2563eb', color: '#fff',
                     border: 'none', borderRadius: 6,
                     cursor: 'pointer' }}>
            Run Scoring
          </button>
          <button onClick={runScoresOverride}
            style={{ padding: '8px 10px', fontSize: 11,
                     background: '#f97316', color: '#fff',
                     border: 'none', borderRadius: 6,
                     cursor: 'pointer' }}>
            Override DO NOT TRADE
          </button>
          <button
            onClick={runLayer3}
            disabled={l3Running}
            style={{
              padding: '8px 10px',
              fontSize: 11,
              background: l3Running ? '#9ca3af' : '#111827',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: l3Running ? 'not-allowed' : 'pointer',
            }}
          >
            {l3Running ? 'Running Layer 3...' : 'Run Layer 3'}
          </button>
        </div>
      </div>

      {data?.regime === 'TRENDING_BULL' && (
        <div style={{
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: 8,
          padding: '10px 14px',
          marginBottom: 8,
          fontSize: 13,
          color: '#1e40af',
        }}>
          TRENDING BULL regime — short signals need score ≥ 82; weaker shorts are
          suppressed.
        </div>
      )}

      {data?.rotation_alerts?.map((alert, i) => (
        <div key={i} style={{
          background: '#fefce8', border: '1px solid #fde047',
          borderRadius: 8, padding: '10px 14px', marginBottom: 8,
          fontSize: 13, color: '#713f12',
        }}>
          ⚡ <strong>Sector Rotation:</strong> {alert.message}
        </div>
      ))}

      {successMsg && (
        <div style={{
          padding: '12px 16px', background: '#ecfdf5',
          border: '1px solid #6ee7b7', borderRadius: 8,
          fontSize: 13, color: '#065f46', marginBottom: 12,
        }}>
          {successMsg}
        </div>
      )}

      {error && (
        <div style={{ padding: '12px 16px', background: '#fef2f2',
                      border: '1px solid #fca5a5', borderRadius: 8,
                      fontSize: 13, color: '#991b1b', marginBottom: 12 }}>
          {error}
        </div>
      )}

      {/* Long (BUY) side */}
      {sortedScores.map((score) => {
        const sigStyle = SIGNAL_COLORS[score.signal] || SIGNAL_COLORS.watch
        const velColor = VELOCITY_COLORS[score.velocity_label] || '#6b7280'
        const isOpen   = expanded === score.ticker
        const barWidth = `${score.buy_score}%`

        return (
          <div key={score.ticker}
            style={{ border: '1px solid #e5e7eb', borderRadius: 10,
                     marginBottom: 8, overflow: 'hidden',
                     background: '#fff' }}>
            <div
              onClick={() => setExpanded(isOpen ? null : score.ticker)}
              style={{ padding: '12px 16px', cursor: 'pointer',
                       display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ minWidth: 110 }}>
                <div style={{ fontWeight: 600, fontSize: 15,
                               display: 'flex', alignItems: 'center',
                               gap: 6 }}>
                  {score.ticker}
                  {score.is_breakout && (
                    <span style={{ fontSize: 12, color: '#ca8a04' }}>⚡</span>
                  )}
                  {sortBy === 'confidence_desc' || sortBy === 'confidence_asc' ? (
                    l3Signals[score.ticker] ? (
                      <span style={{
                        fontSize: 10, background: '#eff6ff',
                        color: '#2563eb', padding: '1px 6px', borderRadius: 8,
                      }}>
                        Conf: {l3Signals[score.ticker].toFixed(0)}
                      </span>
                    ) : null
                  ) : sortBy === 'rsi_neutral' ? (
                    <span style={{
                      fontSize: 10, background: '#f9fafb',
                      color: '#6b7280', padding: '1px 6px', borderRadius: 8,
                    }}>
                      RSI sort
                    </span>
                  ) : null}
                </div>
                <div style={{ fontSize: 11, color: '#6b7280' }}>
                  {score.sector}
                </div>
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between',
                              alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>
                    {score.buy_score.toFixed(1)}
                  </span>
                  <span style={{ fontSize: 11,
                                  background: sigStyle.bg,
                                  color: sigStyle.text,
                                  padding: '1px 8px', borderRadius: 10 }}>
                    {score.signal.replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ height: 6, background: '#f3f4f6',
                              borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{
                    width:      barWidth,
                    height:     '100%',
                    background: score.buy_score >= 70 ? '#16a34a'
                              : score.buy_score >= 55 ? '#ca8a04'
                              : '#6b7280',
                    borderRadius: 3,
                    transition: 'width 0.5s ease',
                  }} />
                </div>
              </div>

              <div style={{ textAlign: 'right', minWidth: 80 }}>
                <div style={{ fontSize: 12, color: velColor,
                               fontWeight: 500 }}>
                  {score.score_delta >= 0 ? '+' : ''}
                  {score.score_delta.toFixed(1)}
                </div>
                <div style={{ fontSize: 11, color: velColor }}>
                  {score.velocity_label.replace(/_/g, ' ')}
                </div>
              </div>
            </div>

            {isOpen && (
              <div style={{ padding: '0 16px 14px',
                            borderTop: '1px solid #f3f4f6' }}>
                <p style={{ fontSize: 13, color: '#374151',
                             lineHeight: 1.6, margin: '10px 0 10px' }}>
                  {score.catalyst_summary}
                </p>
                <div style={{ display: 'grid',
                              gridTemplateColumns: '1fr 1fr',
                              gap: '6px 16px' }}>
                  {Object.entries(score.score_breakdown || {})
                    .sort(([,a], [,b]) => b - a)
                    .map(([factor, pts]) => (
                      <div key={factor}>
                        <div style={{ display: 'flex',
                                      justifyContent: 'space-between',
                                      fontSize: 11, color: '#6b7280',
                                      marginBottom: 2 }}>
                          <span>{factor.replace(/_/g, ' ')}</span>
                          <span style={{ fontWeight: 500,
                                          color: '#374151' }}>
                            {pts.toFixed(1)}
                          </span>
                        </div>
                        <div style={{ height: 4,
                                      background: '#f3f4f6',
                                      borderRadius: 2 }}>
                          <div style={{
                            width:    `${(pts / 22) * 100}%`,
                            maxWidth: '100%',
                            height:   '100%',
                            background: '#2563eb',
                            borderRadius: 2,
                          }} />
                        </div>
                      </div>
                    ))}
                </div>
                <TechnicalCard ticker={score.ticker} direction="BUY" />
                {score.flags?.length > 0 && (
                  <div style={{ marginTop: 10, display: 'flex',
                                gap: 6, flexWrap: 'wrap' }}>
                    {score.flags.map(flag => (
                      <span key={flag}
                        style={{ fontSize: 10, padding: '2px 8px',
                                  background: '#fef9c3',
                                  color: '#854d0e',
                                  borderRadius: 10 }}>
                        ⚠ {flag.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
                {score.streak_days > 1 && (
                  <p style={{ marginTop: 8, fontSize: 12,
                               color: '#16a34a' }}>
                    🔥 {score.streak_days} consecutive days above 60
                  </p>
                )}
              </div>
            )}
          </div>
        )
      })}

      {data?.top_scores?.length === 0 && !error && (
        <div style={{ padding: 20, textAlign: 'center',
                      fontSize: 13, color: '#6b7280',
                      background: '#f9fafb', borderRadius: 8 }}>
          No companies above threshold today.
          {data?.regime === 'DO_NOT_TRADE' && ' (Do Not Trade day)'}
        </div>
      )}

      {/* Short signals section — always visible */}
      <div style={{ marginTop: 32 }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
        }}>
          <div>
            <h2 style={{
              fontSize: 18,
              fontWeight: 600,
              margin: 0,
              color: '#991b1b',
            }}>
              Today's SHORT Signals
            </h2>
            <p style={{
              fontSize: 12,
              color: '#6b7280',
              margin: '4px 0 0',
            }}>
              {shortData.length > 0
                ? `${shortData.length} companies with bearish signals`
                : data?.regime === 'TRENDING_BULL'
                ? 'Shorts suppressed in TRENDING BULL regime (need score ≥ 82)'
                : 'No short signals above threshold today'}
            </p>
          </div>
        </div>

        {shortData.length === 0 ? (
          <div style={{
            padding: '20px 16px',
            background: '#fef2f2',
            borderRadius: 10,
            border: '1px solid #fecaca',
            fontSize: 13,
            color: '#991b1b',
            textAlign: 'center',
          }}>
            {data?.regime === 'TRENDING_BULL'
              ? '⚠ TRENDING BULL regime — short signals require score ≥ 82. No strong short candidates today.'
              : 'No short signals found. Run scoring to check for bearish setups.'}
          </div>
        ) : (
          sortedShorts.map((sc) => (
            <ShortSignalCard key={sc.ticker} score={sc} />
          ))
        )}
      </div>
    </div>
  )
}

