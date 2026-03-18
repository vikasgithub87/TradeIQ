/**
 * TechnicalCard.tsx — Technical validation display for a company.
 * Shows confidence score, entry/target/SL, indicator snapshot,
 * and confluence breakdown. Displayed inline in ScoresPanel.
 */
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string

interface Signal {
  ticker:              string
  direction:           string
  confidence_score:    number
  final_signal:        string
  technical_alignment: string
  agreeing_signals:    number
  total_signals:       number
  entry_low:           number
  entry_high:          number
  target_1:            number
  target_2:            number
  stop_loss:           number
  risk_reward:         number
  expected_move_pct:   number
  rsi:                 number | null
  macd_crossover:      string | null
  ema_trend:           string | null
  volume_ratio:        number | null
  vwap:                number | null
  vwap_position:       string | null
  pdh:                 number | null
  pdl:                 number | null
  pdh_breakout:        boolean
  pdl_breakdown:       boolean
  patterns:            string[]
  dominant_pattern:    string
  penalty_reasons:     string[]
  confluence_detail:   Array<{ indicator: string; agrees: boolean }>
  week52_high_pct:       number | null
  week52_low_pct:        number | null
  near_52w_high:         boolean
  near_52w_low:          boolean
  exhaustion_risk:       boolean
  reversal_potential:    boolean
  market_cap_cr:         number | null
  cap_category:          string
  invalidation_triggered:boolean
  invalidation_note:     string | null
  sector:                string
  sector_theme_score:    number
  sector_signal:         string
  sector_confirming:     boolean
  time_quality:          number
  optimal_entry_window:  boolean
}

interface Props { ticker: string; direction?: string }

export default function TechnicalCard({ ticker }: Props) {
  const [signal, setSignal] = useState<Signal | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!ticker) return
    setLoading(true)
    setError(null)
    axios.get(`${API_URL}/signals/company/${ticker}`)
      .then(res => {
        setSignal(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError(
          err.response?.status === 404
            ? `Run Layer 3 for ${ticker} first`
            : 'Error loading signal'
        )
        setLoading(false)
      })
  }, [ticker])

  const runSignal = () => {
    setLoading(true)
    axios.post(`${API_URL}/signals/run?ticker=${ticker}`)
      .then(() => {
        axios.get(`${API_URL}/signals/company/${ticker}`)
          .then(res => { setSignal(res.data); setLoading(false) })
          .catch(() => setLoading(false))
      })
      .catch(() => setLoading(false))
  }

  if (loading) return (
    <div style={{ padding: 12, fontSize: 12, color: '#6b7280' }}>
      Validating technically...
    </div>
  )

  const isBuy = signal?.direction === 'BUY'
  const confScore = signal?.confidence_score || 0
  const confColor = confScore >= 70 ? '#16a34a'
    : confScore >= 50 ? '#ca8a04'
    : '#dc2626'
  const dirColor = isBuy ? '#16a34a' : '#dc2626'

  return (
    <div style={{
      marginTop: 10,
      border: `1px solid ${isBuy ? '#86efac' : '#fca5a5'}`,
      borderRadius: 10,
      background: isBuy ? '#f0fdf4' : '#fef2f2',
      overflow: 'hidden',
    }}>

      {!signal ? (
        <div style={{
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}>
          <span style={{ fontSize: 12, color: '#6b7280' }}>
            {error || 'No technical validation yet'}
          </span>
          <button
            onClick={runSignal}
            style={{
              fontSize: 12,
              padding: '4px 12px',
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Validate Now
          </button>
        </div>
      ) : (
        <>
          <div style={{
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${isBuy ? '#86efac' : '#fca5a5'}`,
            gap: 12,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{
                background: dirColor,
                color: '#fff',
                fontSize: 11,
                fontWeight: 600,
                padding: '2px 10px',
                borderRadius: 10,
              }}>
                {signal.direction} {isBuy ? '▲' : '▼'}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, color: confColor }}>
                Confidence: {confScore.toFixed(0)}/100
              </span>
              <span style={{ fontSize: 12, color: '#6b7280' }}>
                {signal.agreeing_signals}/{signal.total_signals} signals agree
              </span>
            </div>
            <span style={{
              fontSize: 11,
              background: signal.final_signal.includes('HIGH') ? '#dcfce7' : '#fef9c3',
              color: signal.final_signal.includes('HIGH') ? '#15803d' : '#854d0e',
              padding: '2px 8px',
              borderRadius: 10,
              whiteSpace: 'nowrap',
            }}>
              {signal.final_signal.replace(/_/g, ' ')}
            </span>
          </div>

          {signal.invalidation_triggered && signal.invalidation_note && (
            <div style={{
              padding: '8px 16px',
              background: '#fef2f2',
              borderLeft: '4px solid #dc2626',
              fontSize: 12,
              color: '#991b1b',
              fontWeight: 500,
            }}>
              {signal.invalidation_note}
            </div>
          )}

          <div style={{
            padding: '10px 16px',
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 8,
            borderBottom: `1px solid ${isBuy ? '#86efac' : '#fca5a5'}`,
          }}>
            {[
              { label: 'Entry', value: `₹${signal.entry_low}–${signal.entry_high}` },
              { label: 'Target 1', value: `₹${signal.target_1}`, color: '#16a34a' },
              { label: 'Stop Loss', value: `₹${signal.stop_loss}`, color: '#dc2626' },
              {
                label: 'R:R',
                value: `${signal.risk_reward}×`,
                color: signal.risk_reward >= 1.5 ? '#16a34a' : '#ca8a04',
              },
            ].map(item => (
              <div key={item.label}>
                <div style={{
                  fontSize: 10,
                  color: '#6b7280',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  marginBottom: 2,
                }}>
                  {item.label}
                </div>
                <div style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: item.color || '#111827',
                }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>

          <div style={{
            padding: '10px 16px',
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
            fontSize: 11,
            color: '#6b7280',
          }}>
            {signal.rsi !== null && (
              <span>
                RSI <strong style={{
                  color: signal.rsi > 70 ? '#dc2626'
                    : signal.rsi < 30 ? '#16a34a'
                      : '#374151',
                }}>
                  {signal.rsi?.toFixed(0)}
                </strong>
              </span>
            )}
            {signal.macd_crossover && (
              <span>
                MACD <strong style={{
                  color: signal.macd_crossover.includes('bullish') ? '#16a34a' : '#dc2626',
                }}>
                  {signal.macd_crossover.replace(/_/g, ' ')}
                </strong>
              </span>
            )}
            {signal.ema_trend && (
              <span>Trend <strong>{signal.ema_trend.replace(/_/g, ' ')}</strong></span>
            )}
            {signal.volume_ratio !== null && (
              <span>
                Vol <strong style={{
                  color: (signal.volume_ratio || 0) >= 1.5 ? '#16a34a' : '#6b7280',
                }}>
                  {signal.volume_ratio?.toFixed(1)}×
                </strong>
              </span>
            )}
            {signal.vwap_position && (
              <span>
                VWAP <strong style={{
                  color: signal.vwap_position.includes('above') ? '#16a34a' : '#dc2626',
                }}>
                  {signal.vwap_position.replace(/_/g, ' ')}
                </strong>
              </span>
            )}
            {signal.pdh_breakout && (
              <span style={{ color: '#16a34a', fontWeight: 600 }}>
                PDH breakout ▲
              </span>
            )}
            {signal.pdl_breakdown && (
              <span style={{ color: '#dc2626', fontWeight: 600 }}>
                PDL breakdown ▼
              </span>
            )}
            {signal.dominant_pattern !== 'none' && signal.dominant_pattern && (
              <span>Pattern <strong>{signal.dominant_pattern}</strong></span>
            )}
          </div>

          {/* Context row — 52W, cap, sector, time */}
          <div style={{
            padding: '8px 16px 12px',
            display: 'flex',
            gap: 10,
            flexWrap: 'wrap',
            fontSize: 11,
            borderTop: `1px solid ${isBuy ? '#86efac' : '#fca5a5'}`,
          }}>

            {/* Market cap category */}
            {signal.cap_category && signal.cap_category !== 'Unknown' && (
              <span style={{
                background: '#f0f9ff',
                color: '#0369a1',
                padding: '2px 8px',
                borderRadius: 10,
                fontWeight: 500,
              }}>
                {signal.cap_category}
                {signal.market_cap_cr
                  ? ` · ₹${(signal.market_cap_cr / 100).toFixed(0)}K Cr`
                  : ''}
              </span>
            )}

            {/* 52-week position */}
            {signal.near_52w_high && (
              <span style={{
                background: '#fef9c3',
                color: '#854d0e',
                padding: '2px 8px',
                borderRadius: 10,
                fontWeight: 500,
              }}>
                ⚠ Near 52W High
                {signal.week52_high_pct !== null
                  ? ` (${signal.week52_high_pct?.toFixed(1)}% away)`
                  : ''}
              </span>
            )}

            {signal.near_52w_low && (
              <span style={{
                background: '#f0fdf4',
                color: '#15803d',
                padding: '2px 8px',
                borderRadius: 10,
                fontWeight: 500,
              }}>
                Near 52W Low — bounce zone
                {signal.week52_low_pct !== null
                  ? ` (${signal.week52_low_pct?.toFixed(1)}% from low)`
                  : ''}
              </span>
            )}

            {signal.exhaustion_risk && (
              <span style={{
                background: '#fee2e2',
                color: '#991b1b',
                padding: '2px 8px',
                borderRadius: 10,
              }}>
                Exhaustion risk at resistance
              </span>
            )}

            {/* Sector momentum */}
            {signal.sector && (
              <span style={{
                background: signal.sector_confirming ? '#f0fdf4' : '#fef2f2',
                color: signal.sector_confirming ? '#15803d' : '#991b1b',
                padding: '2px 8px',
                borderRadius: 10,
              }}>
                {signal.sector} sector:
                {signal.sector_confirming ? ' ✓ confirming' : ' ✗ not confirming'}
                {signal.sector_theme_score > 0
                  ? ` (${signal.sector_theme_score.toFixed(0)})`
                  : ''}
              </span>
            )}

            {/* Entry window quality */}
            {signal.optimal_entry_window === false && (
              <span style={{
                background: '#fff7ed',
                color: '#c2410c',
                padding: '2px 8px',
                borderRadius: 10,
              }}>
                ⏰ Outside optimal entry window
              </span>
            )}

          </div>

          {signal.penalty_reasons?.length > 0 && (
            <div style={{
              padding: '6px 16px 10px',
              display: 'flex',
              gap: 6,
              flexWrap: 'wrap',
            }}>
              {signal.penalty_reasons.map(r => (
                <span key={r} style={{
                  fontSize: 10,
                  padding: '2px 8px',
                  background: '#fef9c3',
                  color: '#854d0e',
                  borderRadius: 10,
                }}>
                  ⚠ {r}
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

