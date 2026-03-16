/**
 * App.tsx — Router with auth guard
 */
import { useEffect, useState } from 'react'
import { supabase, isSupabaseConfigured } from './lib/supabase'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

export default function App() {
  const [session, setSession] = useState<any>(undefined)

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setSession(null)
      return
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
    }).catch(() => setSession(null))
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => setSession(session)
    )
    return () => subscription.unsubscribe()
  }, [])

  if (!isSupabaseConfigured) {
    return (
      <div style={{ maxWidth: 480, margin: '60px auto', padding: 24, fontFamily: 'sans-serif' }}>
        <h1 style={{ fontSize: 22, marginBottom: 8 }}>TradeIQ</h1>
        <p style={{ color: '#666', marginBottom: 16 }}>Configure Supabase to use login and dashboard.</p>
        <div style={{ padding: 16, background: '#fef3c7', borderRadius: 8, fontSize: 14 }}>
          <p style={{ margin: '0 0 8px', fontWeight: 600 }}>Steps:</p>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>Open <code>frontend/.env.local</code></li>
            <li>Set <code>VITE_SUPABASE_URL</code> to your Supabase project URL</li>
            <li>Set <code>VITE_SUPABASE_ANON_KEY</code> to your Supabase anon key</li>
            <li>Save and refresh this page</li>
          </ol>
        </div>
      </div>
    )
  }

  if (session === undefined) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center',
                    alignItems: 'center', height: '100vh',
                    fontFamily: 'sans-serif', color: '#666' }}>
        Loading...
      </div>
    )
  }

  return session ? <Dashboard /> : <Login />
}
