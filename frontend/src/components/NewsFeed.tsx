/**
 * NewsFeed.tsx — Live news feed for a selected company.
 */
import { useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string

interface Catalyst {
  type: string
  headline: string
  source: string
  source_trust: number
  intensity: number
  key_fact: string
  intraday_relevance: string
}

interface IntelData {
  ticker: string
  company_name: string
  dominant_direction: string
  net_sentiment_score: number
  intraday_relevance: string
  catalyst_summary: string
  long_catalysts: Catalyst[]
  short_catalysts: Catalyst[]
  timestamp: string
}

const DIRECTION_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  LONG: { bg: '#f0fdf4', color: '#16a34a', label: 'LONG  ▲' },
  SHORT: { bg: '#fef2f2', color: '#dc2626', label: 'SHORT ▼' },
  NEUTRAL: { bg: '#f9fafb', color: '#6b7280', label: 'NEUTRAL ─' },
}

export default function NewsFeed() {
  const [ticker, setTicker] = useState('')
  const [intel, setIntel] = useState<IntelData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchIntel = async (t: string) => {
    if (!t) return
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_URL}/intel/${t.toUpperCase()}`)
      setIntel(res.data)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError(`No data for ${t.toUpperCase()} today. Run Layer 1 first.`)
      } else {
        setError('Cannot reach backend')
      }
      setIntel(null)
    } finally {
      setLoading(false)
    }
  }

  const runIntel = async () => {
    if (!ticker) return
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/intel/run`, {
        ticker: ticker.toUpperCase(),
      })
      setIntel(res.data)
    } catch (err: any) {
      setError('Failed to run intelligence pipeline')
    } finally {
      setLoading(false)
    }
  }

  const dirStyle = DIRECTION_STYLE[intel?.dominant_direction || 'NEUTRAL']

  return (
    <div style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          value={ticker}
          onChange={e => setTicker(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === 'Enter' && fetchIntel(ticker)}
          placeholder="Enter ticker (e.g. RELIANCE)"
          style={{
            flex: 1,
            padding: '8px 12px',
            fontSize: 14,
            border: '1px solid #e5e7eb',
            borderRadius: 6,
          }}
        />
        <button
          onClick={() => fetchIntel(ticker)}
          disabled={loading}
          style={{
            padding: '8px 16px',
            fontSize: 13,
            cursor: 'pointer',
            background: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? '...' : 'Load'}
        </button>
        <button
          onClick={runIntel}
          disabled={loading}
          style={{
            padding: '8px 16px',
            fontSize: 13,
            cursor: 'pointer',
            background: '#059669',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            opacity: loading ? 0.7 : 1,
          }}
        >
          Run Now
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: '10px 14px',
            background: '#fef2f2',
            border: '1px solid #fca5a5',
            borderRadius: 8,
            fontSize: 13,
            color: '#991b1b',
            marginBottom: 12,
          }}
        >
          {error}
        </div>
      )}

      {intel && (
        <div>
          <div
            style={{
              background: dirStyle.bg,
              border: `1px solid ${dirStyle.color}33`,
              borderRadius: 10,
              padding: '14px 18px',
              marginBottom: 16,
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 8,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontWeight: 600, fontSize: 16 }}>
                  {intel.ticker}
                </span>
                <span style={{ fontSize: 13, color: '#6b7280' }}>
                  {intel.company_name}
                </span>
                <span
                  style={{
                    background: dirStyle.color,
                    color: '#fff',
                    fontSize: 12,
                    fontWeight: 600,
                    padding: '2px 10px',
                    borderRadius: 20,
                  }}
                >
                  {dirStyle.label}
                </span>
              </div>
              <span style={{ fontSize: 12, color: '#9ca3af' }}>
                {new Date(intel.timestamp).toLocaleTimeString('en-IN')}
              </span>
            </div>
            <p
              style={{
                margin: 0,
                fontSize: 13,
                color: '#374151',
                lineHeight: 1.6,
              }}
            >
              {intel.catalyst_summary}
            </p>
          </div>

          {intel.long_catalysts.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#16a34a',
                  marginBottom: 6,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Long Catalysts ({intel.long_catalysts.length})
              </div>
              {intel.long_catalysts.map((c, i) => (
                <CatalystCard key={i} catalyst={c} direction="long" />
              ))}
            </div>
          )}

          {intel.short_catalysts.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#dc2626',
                  marginBottom: 6,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Short Catalysts ({intel.short_catalysts.length})
              </div>
              {intel.short_catalysts.map((c, i) => (
                <CatalystCard key={i} catalyst={c} direction="short" />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function CatalystCard({
  catalyst,
  direction,
}: {
  catalyst: Catalyst
  direction: 'long' | 'short'
}) {
  const isLong = direction === 'long'
  const borderCol = isLong ? '#86efac' : '#fca5a5'
  const badgeColor = isLong ? '#16a34a' : '#dc2626'
  const trustPct = Math.round(catalyst.source_trust * 100)
  const trustColor =
    trustPct >= 80 ? '#16a34a' : trustPct >= 60 ? '#ca8a04' : '#dc2626'

  return (
    <div
      style={{
        border: `1px solid ${borderCol}`,
        borderRadius: 8,
        padding: '10px 14px',
        marginBottom: 6,
        background: '#fff',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 8,
          marginBottom: 4,
        }}
      >
        <span
          style={{
            fontSize: 13,
            fontWeight: 500,
            flex: 1,
            color: '#111827',
            lineHeight: 1.4,
          }}
        >
          {catalyst.headline}
        </span>
        <span
          style={{
            background: badgeColor,
            color: '#fff',
            fontSize: 10,
            padding: '1px 6px',
            borderRadius: 10,
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          {catalyst.type.replace(/_/g, ' ')}
        </span>
      </div>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>
        {catalyst.key_fact}
      </div>
      <div
        style={{
          display: 'flex',
          gap: 10,
          fontSize: 11,
          color: '#9ca3af',
        }}
      >
        <span>{catalyst.source}</span>
        <span style={{ color: trustColor }}>Trust: {trustPct}%</span>
        <span>Intensity: {Math.round(catalyst.intensity * 100)}%</span>
        <span
          style={{
            color:
              catalyst.intraday_relevance === 'HIGH'
                ? '#16a34a'
                : catalyst.intraday_relevance === 'MEDIUM'
                ? '#ca8a04'
                : '#9ca3af',
          }}
        >
          {catalyst.intraday_relevance}
        </span>
      </div>
    </div>
  )
}

