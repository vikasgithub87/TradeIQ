/**
 * Dashboard.tsx — Protected dashboard, shown after login
 */
import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import axios from 'axios'
import RegimeBanner from '../components/RegimeBanner'
import NewsFeed from '../components/NewsFeed'
import ScoresPanel from '../components/ScoresPanel'
import ScanPanel from '../components/ScanPanel'

const API_URL = import.meta.env.VITE_API_URL as string

export default function Dashboard() {
  const [user,       setUser]       = useState<any>(null)
  const [apiStatus,  setApiStatus]  = useState<string>('checking...')
  const [dbStatus,   setDbStatus]   = useState<string>('checking...')

  useEffect(() => {
    // Get current user
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user)
    })
    // Check backend health
    axios.get(`${API_URL}/health`)
      .then(res => {
        setApiStatus(res.data.status === 'ok' ? '✓ Connected' : '✗ Error')
        setDbStatus(res.data.db === 'connected' ? '✓ Connected' : '✗ Disconnected')
      })
      .catch(() => {
        setApiStatus('✗ Cannot reach backend')
        setDbStatus('✗ Unknown')
      })
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.reload()
  }

  const statusStyle = (s: string) => ({
    color: s.startsWith('✓') ? '#065f46' : s.startsWith('✗') ? '#991b1b' : '#92400e',
    fontWeight: 500 as const,
  })

  return (
    <div style={{ maxWidth: 700, margin: '40px auto', padding: 24,
                  fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 24, margin: 0 }}>TradeIQ</h1>
          <p style={{ color: '#666', margin: '4px 0 0', fontSize: 13 }}>
            NSE India Trading Intelligence Platform
          </p>
        </div>
        <button onClick={handleLogout}
          style={{ padding: '6px 14px', fontSize: 13, cursor: 'pointer',
                   border: '1px solid #ddd', borderRadius: 6,
                   background: '#fff' }}>
          Logout
        </button>
      </div>

      <RegimeBanner />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
                    gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Logged in as', value: user?.email || '...' },
          { label: 'Backend API',  value: apiStatus },
          { label: 'Database',     value: dbStatus },
        ].map(({ label, value }) => (
          <div key={label} style={{ padding: '16px', background: '#f9fafb',
                       borderRadius: 8, border: '1px solid #e5e7eb' }}>
            <p style={{ margin: '0 0 4px', fontSize: 11,
                        color: '#6b7280', textTransform: 'uppercase',
                        letterSpacing: '0.05em' }}>{label}</p>
            <p style={{ margin: 0, fontSize: 14, ...statusStyle(value) }}>
              {value}
            </p>
          </div>
        ))}
      </div>

      <div style={{ padding: 20, background: '#eff6ff', borderRadius: 8,
                    border: '1px solid #bfdbfe' }}>
        <h2 style={{ fontSize: 16, margin: '0 0 8px', color: '#1e40af' }}>
          Sprint 1 & 2 Complete
        </h2>
        <p style={{ margin: 0, fontSize: 13, color: '#1e40af', lineHeight: 1.6 }}>
          Foundation ready. Backend API. Database. Auth. Layer 0 Market Regime DNA live.
        </p>
      </div>

      <div style={{ marginTop: 32 }}>
        <h2 style={{ fontSize: 18, marginBottom: 4, fontWeight: 600 }}>
          Company Intelligence
        </h2>
        <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 0 }}>
          Enter a ticker to load today&apos;s news analysis
        </p>
        <NewsFeed />
      </div>

      <div style={{ marginTop: 32 }}>
        <ScanPanel onScanComplete={() => window.location.reload()} />
        <ScoresPanel />
      </div>
    </div>
  )
}
