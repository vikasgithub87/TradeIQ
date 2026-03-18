/**
 * NewsMapped.tsx — Breaking news mapped to impacted stocks.
 * Shows today's top headlines, themes extracted, and which
 * stocks are affected. Appears above ScanPanel on dashboard.
 */
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string

interface Headline {
  headline: string
  source: string
  published_at: string
  url: string
}

interface Company {
  ticker: string
  name: string
  sector: string
  reason: string
  strength: string
}

interface NewsFeedData {
  date: string
  themes: string[]
  market_sentiment: string
  key_risk: string
  headline_count: number
  headlines: Headline[]
  companies: Company[]
  method: string
}

const STRENGTH_STYLE: Record<string, { bg: string; color: string }> = {
  HIGH: { bg: '#fee2e2', color: '#991b1b' },
  MEDIUM: { bg: '#fef9c3', color: '#854d0e' },
  LOW: { bg: '#f3f4f6', color: '#6b7280' },
}

const SENTIMENT_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  bullish: { bg: '#f0fdf4', color: '#15803d', label: 'Bullish' },
  bearish: { bg: '#fef2f2', color: '#991b1b', label: 'Bearish' },
  mixed: { bg: '#fefce8', color: '#854d0e', label: 'Mixed' },
}

export default function NewsMapped() {
  const [data, setData] = useState<NewsFeedData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [running, setRunning] = useState(false)

  const fetchFeed = () => {
    setLoading(true)
    setError(null)
    axios.get(`${API_URL}/newsfeed/today`)
      .then(res => { setData(res.data); setLoading(false) })
      .catch(err => {
        setError(
          err.response?.status === 404
            ? 'not_run'
            : 'Error loading news feed'
        )
        setLoading(false)
      })
  }

  const runScan = () => {
    setRunning(true)
    axios.post(`${API_URL}/newsfeed/run?use_claude=true`)
      .then(() => { fetchFeed(); setRunning(false) })
      .catch(() => { setRunning(false) })
  }

  useEffect(() => { fetchFeed() }, [])

  if (loading) return null

  const sentStyle = SENTIMENT_STYLE[data?.market_sentiment || 'mixed']

  return (
    <div style={{
      border: '1px solid #e5e7eb',
      borderRadius: 12,
      overflow: 'hidden',
      marginBottom: 16,
      background: '#fff',
    }}>
      <div style={{
        padding: '12px 18px',
        background: '#fafafa',
        borderBottom: '1px solid #f3f4f6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>
            Breaking News → Impacted Stocks
          </span>
          {data && (
            <span style={{
              fontSize: 11,
              background: sentStyle.bg,
              color: sentStyle.color,
              padding: '2px 8px',
              borderRadius: 10,
              fontWeight: 500,
            }}>
              Market: {sentStyle.label}
            </span>
          )}
          {data?.method === 'claude' && (
            <span style={{
              fontSize: 10,
              background: '#eff6ff',
              color: '#2563eb',
              padding: '1px 6px',
              borderRadius: 8,
            }}>
              AI mapped
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              fontSize: 12,
              padding: '4px 12px',
              border: '1px solid #e5e7eb',
              borderRadius: 6,
              background: '#fff',
              cursor: 'pointer',
              color: '#374151',
            }}
          >
            {expanded ? 'Hide headlines' : 'Show headlines'}
          </button>
          <button
            onClick={runScan}
            disabled={running}
            style={{
              fontSize: 12,
              padding: '4px 12px',
              border: 'none',
              borderRadius: 6,
              background: running ? '#9ca3af' : '#2563eb',
              color: '#fff',
              cursor: running ? 'not-allowed' : 'pointer',
            }}
          >
            {running ? 'Scanning...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error === 'not_run' && (
        <div style={{
          padding: '16px 18px',
          fontSize: 13,
          color: '#6b7280',
          textAlign: 'center',
        }}>
          Click Refresh to scan today's breaking news and map to stocks
        </div>
      )}

      {data && (
        <>
          {data.themes?.length > 0 && (
            <div style={{
              padding: '8px 18px',
              display: 'flex',
              gap: 6,
              flexWrap: 'wrap',
              borderBottom: '1px solid #f3f4f6',
            }}>
              <span style={{ fontSize: 11, color: '#6b7280', alignSelf: 'center' }}>
                Themes:
              </span>
              {data.themes.map(theme => (
                <span key={theme} style={{
                  fontSize: 11,
                  background: '#f0f9ff',
                  color: '#0369a1',
                  padding: '2px 8px',
                  borderRadius: 10,
                }}>
                  {theme}
                </span>
              ))}
            </div>
          )}

          {data.key_risk && (
            <div style={{
              padding: '6px 18px',
              fontSize: 12,
              color: '#854d0e',
              background: '#fffbeb',
              borderBottom: '1px solid #fde68a',
            }}>
              ⚠ Key risk today: {data.key_risk}
            </div>
          )}

          {expanded && data.headlines?.length > 0 && (
            <div style={{
              padding: '10px 18px',
              borderBottom: '1px solid #f3f4f6',
              maxHeight: 240,
              overflowY: 'auto',
            }}>
              {data.headlines.slice(0, 15).map((h, i) => (
                <div key={i} style={{
                  padding: '6px 0',
                  borderBottom: i < 14 ? '1px solid #f9fafb' : 'none',
                  display: 'flex',
                  gap: 10,
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, color: '#374151', lineHeight: 1.4 }}>
                      {h.headline}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                      {h.source}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ padding: '10px 18px' }}>
            <div style={{
              fontSize: 11,
              fontWeight: 500,
              color: '#6b7280',
              marginBottom: 8,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}>
              {data.companies?.length || 0} stocks impacted by today's news
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 6,
            }}>
              {(data.companies || []).slice(0, 12).map(company => {
                const sStyle = STRENGTH_STYLE[company.strength] || STRENGTH_STYLE.MEDIUM
                return (
                  <div key={company.ticker} style={{
                    border: '1px solid #e5e7eb',
                    borderRadius: 8,
                    padding: '8px 10px',
                    background: '#fafafa',
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      marginBottom: 3,
                    }}>
                      <span style={{ fontWeight: 600, fontSize: 13, color: '#111827' }}>
                        {company.ticker}
                      </span>
                      <span style={{
                        fontSize: 10,
                        background: sStyle.bg,
                        color: sStyle.color,
                        padding: '1px 6px',
                        borderRadius: 8,
                        fontWeight: 500,
                      }}>
                        {company.strength}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: '#6b7280', lineHeight: 1.4 }}>
                      {company.reason || company.sector}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

