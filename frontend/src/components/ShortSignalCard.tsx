/**
 * ShortSignalCard.tsx — Expandable card for a single SHORT signal.
 */
import { useState } from 'react'
import TechnicalCard from './TechnicalCard'

export interface ShortScore {
  ticker: string
  short_score: number
  short_signal: string
  short_breakdown: Record<string, number>
  short_top_factors: string[]
  short_flags: string[]
  sector: string
  score_delta: number
  velocity_label: string
  is_breakout: boolean
  streak_days: number
  catalyst_summary: string
  recommended_direction?: string
  direction_reason?: string
  l3_flags?: string[]
}

const SHORT_SIGNAL_COLORS: Record<string, { bg: string; text: string }> = {
  strong_short: { bg: '#fee2e2', text: '#991b1b' },
  short: { bg: '#fecaca', text: '#7f1d1d' },
  moderate_short: { bg: '#fef9c3', text: '#854d0e' },
  watch_short: { bg: '#f3f4f6', text: '#374151' },
  no_short: { bg: '#f9fafb', text: '#9ca3af' },
}

const SHORT_FACTOR_MAX: Record<string, number> = {
  negative_news: 25,
  earnings_miss: 20,
  fii_selling: 15,
  short_oi_buildup: 15,
  promoter_pledge: 12,
  sector_headwind: 8,
  exhaustion_signal: 5,
}

interface Props {
  score: ShortScore
}

export default function ShortSignalCard({ score }: Props) {
  const [expanded, setExpanded] = useState(false)
  const sig = score.short_signal || 'no_short'
  const sigStyle = SHORT_SIGNAL_COLORS[sig] || SHORT_SIGNAL_COLORS.no_short
  const barPct = `${Math.min(100, score.short_score || 0)}%`
  const s = score.short_score ?? 0
  const delta = score.score_delta ?? 0

  return (
    <div
      style={{
        border: '1px solid #fca5a5',
        borderRadius: 10,
        marginBottom: 8,
        overflow: 'hidden',
        background: '#fff',
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '12px 16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          background: expanded ? '#fff5f5' : '#fff',
        }}
      >
        <div style={{ minWidth: 110 }}>
          <div
            style={{
              fontWeight: 600,
              fontSize: 15,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              color: '#991b1b',
            }}
          >
            {score.ticker}
            {score.is_breakout && (
              <span style={{ fontSize: 12, color: '#dc2626' }}>⚡</span>
            )}
          </div>
          <div style={{ fontSize: 11, color: '#6b7280' }}>
            {score.sector || '—'}
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 4,
            }}
          >
            <span style={{ fontSize: 13, fontWeight: 600, color: '#991b1b' }}>
              {s.toFixed(1)}
            </span>
            <span
              style={{
                fontSize: 11,
                background: sigStyle.bg,
                color: sigStyle.text,
                padding: '1px 8px',
                borderRadius: 10,
              }}
            >
              {sig.replace(/_/g, ' ')}
            </span>
          </div>
          <div
            style={{ height: 6, background: '#fee2e2', borderRadius: 3, overflow: 'hidden' }}
          >
            <div
              style={{
                width: barPct,
                height: '100%',
                background: s >= 70 ? '#dc2626' : s >= 50 ? '#f97316' : '#9ca3af',
                borderRadius: 3,
                transition: 'width 0.5s ease',
              }}
            />
          </div>
        </div>

        <div style={{ textAlign: 'right', minWidth: 90 }}>
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              background: '#fee2e2',
              color: '#991b1b',
              padding: '2px 8px',
              borderRadius: 10,
              marginBottom: 4,
            }}
          >
            SHORT ▼
          </div>
          <div
            style={{
              fontSize: 11,
              color: delta >= 0 ? '#dc2626' : '#16a34a',
            }}
          >
            {delta >= 0 ? '+' : ''}
            {delta.toFixed(1)}
          </div>
        </div>
      </div>

      {expanded && (
        <div
          style={{
            padding: '0 16px 14px',
            borderTop: '1px solid #fee2e2',
            background: '#fff5f5',
          }}
        >
          <p
            style={{
              fontSize: 13,
              color: '#374151',
              lineHeight: 1.6,
              margin: '10px 0',
            }}
          >
            {score.catalyst_summary || 'No catalyst summary available.'}
          </p>

          {score.direction_reason && (
            <p
              style={{
                fontSize: 12,
                color: '#7f1d1d',
                background: '#fee2e2',
                borderRadius: 6,
                padding: '6px 10px',
                margin: '0 0 10px',
              }}
            >
              Direction: {score.direction_reason}
            </p>
          )}

          <div
            style={{
              fontSize: 12,
              color: '#92400e',
              background: '#fffbeb',
              border: '1px solid #fde68a',
              borderRadius: 6,
              padding: '8px 10px',
              marginBottom: 10,
            }}
          >
            SHORT trade: Sell first, buy back lower. Entry = current price. Target =
            below entry. Stop loss = above entry.
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '6px 16px',
            }}
          >
            {Object.entries(score.short_breakdown || {})
              .sort(([, a], [, b]) => b - a)
              .map(([factor, pts]) => {
                const maxPts = SHORT_FACTOR_MAX[factor] || 25
                return (
                  <div key={factor}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: 11,
                        color: '#6b7280',
                        marginBottom: 2,
                      }}
                    >
                      <span>{factor.replace(/_/g, ' ')}</span>
                      <span style={{ fontWeight: 500, color: '#374151' }}>
                        {Number(pts).toFixed(1)}
                      </span>
                    </div>
                    <div style={{ height: 4, background: '#fee2e2', borderRadius: 2 }}>
                      <div
                        style={{
                          width: `${(Number(pts) / maxPts) * 100}%`,
                          maxWidth: '100%',
                          height: '100%',
                          background: '#dc2626',
                          borderRadius: 2,
                        }}
                      />
                    </div>
                  </div>
                )
              })}
          </div>

          <TechnicalCard ticker={score.ticker} direction="SHORT" />

          {(score.l3_flags || score.short_flags || []).length > 0 && (
            <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {[
                ...new Set([
                  ...(score.l3_flags || []),
                  ...(score.short_flags || []),
                ]),
              ].map((flag) => (
                <span
                  key={flag}
                  style={{
                    fontSize: 10,
                    padding: '2px 8px',
                    background: '#fee2e2',
                    color: '#991b1b',
                    borderRadius: 10,
                  }}
                >
                  {flag.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}

          {(score.streak_days ?? 0) > 1 && (
            <p style={{ marginTop: 8, fontSize: 12, color: '#dc2626' }}>
              {score.streak_days} consecutive days above short threshold
            </p>
          )}
        </div>
      )}
    </div>
  )
}
