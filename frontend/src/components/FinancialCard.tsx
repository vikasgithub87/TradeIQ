/**
 * FinancialCard.tsx — Financial metrics display for a company.
 */
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string

interface FinancialData {
  ticker:              string
  current_price:       number | null
  market_cap_cr:       number | null
  pe_ratio:            number | null
  fii_activity:        string
  promoter_pledge_pct: number
  near_52w_high:       boolean
  near_52w_low:        boolean
  pcr:                 number
  oi_signal:           string
  eps_surprise_pct:    number | null
  surprise_label:      string | null
  in_results_window:   boolean
  fundamentals: {
    week52_high:      number | null
    week52_low:       number | null
    week52_high_pct:  number | null
    week52_low_pct:   number | null
    debt_to_equity?:  number | null
    roe_pct?:         number | null
    beta?:            number | null
  }
  data_quality: {
    overall_confidence: number
  }
}

interface Props { ticker: string }

export default function FinancialCard({ ticker }: Props) {
  const [data,    setData]    = useState<FinancialData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    if (!ticker) return
    if (!API_URL || API_URL === 'undefined') {
      setError('API URL not configured')
      return
    }
    setLoading(true)
    setError(null)
    axios.get(`${API_URL}/financials/${ticker}`)
      .then(res => { setData(res.data); setLoading(false) })
      .catch(err => {
        setError(err.response?.status === 404
          ? `Run financial merge for ${ticker} first`
          : 'Error loading data')
        setLoading(false)
      })
  }, [ticker])

  if (loading) {
    return (
      <div style={{ padding: 12, fontSize: 13, color: '#6b7280' }}>
        Loading financial data...
      </div>
    )
  }
  if (error) {
    return (
      <div style={{ padding: 12, fontSize: 12, color: '#dc2626' }}>
        {error}
      </div>
    )
  }
  if (!data) return null

  const conf    = data.data_quality?.overall_confidence || 0
  const confPct = Math.round(conf * 100)
  const confCol = confPct >= 70 ? '#16a34a'
                : confPct >= 40 ? '#ca8a04' : '#dc2626'

  const fiiColor = data.fii_activity === 'net_buyer'  ? '#16a34a'
                 : data.fii_activity === 'net_seller' ? '#dc2626'
                 : '#6b7280'

  const surpriseColor = (data.eps_surprise_pct || 0) >= 3  ? '#16a34a'
                      : (data.eps_surprise_pct || 0) <= -3 ? '#dc2626'
                      : '#6b7280'

  const Metric = ({
    label, value, color, flag
  }: {
    label: string
    value: string | null
    color?: string
    flag?:  string
  }) => (
    <div style={{ background: '#f9fafb', borderRadius: 8,
                  padding: '10px 12px', border: '1px solid #e5e7eb' }}>
      <div style={{ fontSize: 11, color: '#6b7280',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 15, fontWeight: 600,
                    color: color || '#111827' }}>
        {value || 'N/A'}
      </div>
      {flag && (
        <div style={{ fontSize: 10, marginTop: 2,
                      color: '#ca8a04' }}>{flag}</div>
      )}
    </div>
  )

  return (
    <div style={{ marginTop: 12, border: '1px solid #e5e7eb',
                  borderRadius: 10, padding: '14px 16px',
                  background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>
          Financial Metrics — {data.ticker}
        </span>
        <span style={{ fontSize: 11, color: confCol,
                        background: confCol + '18',
                        padding: '2px 8px', borderRadius: 10 }}>
          Data quality: {confPct}%
        </span>
      </div>

      <div style={{ display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: 8, marginBottom: 12 }}>
        <Metric
          label="Price"
          value={data.current_price ? `₹${data.current_price}` : null}
        />
        <Metric
          label="Market cap"
          value={data.market_cap_cr
            ? `₹${data.market_cap_cr.toLocaleString('en-IN')} Cr`
            : null}
        />
        <Metric
          label="P/E ratio"
          value={data.pe_ratio ? data.pe_ratio.toFixed(1) : null}
        />
        <Metric
          label="FII activity"
          value={data.fii_activity?.replace('_', ' ')}
          color={fiiColor}
        />
        <Metric
          label="PCR"
          value={data.pcr ? data.pcr.toFixed(2) : null}
          color={data.pcr >= 1.1 ? '#16a34a'
               : data.pcr <= 0.7 ? '#dc2626' : '#6b7280'}
        />
        <Metric
          label="OI signal"
          value={data.oi_signal?.replace(/_/g, ' ')}
        />
        {data.eps_surprise_pct !== null && (
          <Metric
            label="EPS surprise"
            value={`${data.eps_surprise_pct >= 0 ? '+' : ''}${data.eps_surprise_pct?.toFixed(1)}%`}
            color={surpriseColor}
            flag={data.surprise_label?.replace(/_/g, ' ')}
          />
        )}
        {data.fundamentals?.week52_high_pct != null && (
          <Metric
            label="vs 52W high"
            value={`${data.fundamentals.week52_high_pct.toFixed(1)}% away`}
            color={data.near_52w_high ? '#ca8a04' : '#6b7280'}
            flag={data.near_52w_high ? '⚠ Near high' : undefined}
          />
        )}
        {data.promoter_pledge_pct > 0 && (
          <Metric
            label="Pledge %"
            value={`${data.promoter_pledge_pct}%`}
            color={data.promoter_pledge_pct > 20 ? '#dc2626'
                 : data.promoter_pledge_pct > 10 ? '#ca8a04' : '#16a34a'}
            flag={data.promoter_pledge_pct > 20 ? '⚠ High risk' : undefined}
          />
        )}
      </div>

      {data.in_results_window && (
        <div style={{ background: '#fffbeb', border: '1px solid #fde68a',
                      borderRadius: 6, padding: '8px 12px',
                      fontSize: 12, color: '#92400e' }}>
          ⚠ Results season active — earnings announcement expected.
          Price may gap on result day.
        </div>
      )}
    </div>
  )
}

