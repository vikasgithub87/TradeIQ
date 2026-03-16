/**
 * Login.tsx — Register and login page using Supabase Auth
 */
import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [mode,     setMode]     = useState<'login' | 'register'>('login')
  const [message,  setMessage]  = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    setMessage('')
    try {
      if (mode === 'register') {
        const { error } = await supabase.auth.signUp({ email, password })
        if (error) throw error
        setMessage('Check your email for a verification link.')
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
      }
    } catch (err: any) {
      setMessage(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: 24,
                  fontFamily: 'sans-serif' }}>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>TradeIQ</h1>
      <p style={{ color: '#666', marginBottom: 24 }}>
        NSE India Trading Intelligence
      </p>
      <div style={{ marginBottom: 12 }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          style={{ width: '100%', padding: '10px 12px', fontSize: 14,
                   border: '1px solid #ddd', borderRadius: 6,
                   boxSizing: 'border-box' }}
        />
      </div>
      <div style={{ marginBottom: 16 }}>
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ width: '100%', padding: '10px 12px', fontSize: 14,
                   border: '1px solid #ddd', borderRadius: 6,
                   boxSizing: 'border-box' }}
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{ width: '100%', padding: '10px 12px', fontSize: 14,
                 background: '#2563eb', color: '#fff', border: 'none',
                 borderRadius: 6, cursor: loading ? 'not-allowed' : 'pointer',
                 opacity: loading ? 0.7 : 1 }}
      >
        {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Register'}
      </button>
      <p style={{ marginTop: 12, textAlign: 'center', fontSize: 13,
                  color: '#2563eb', cursor: 'pointer' }}
         onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
        {mode === 'login'
          ? "Don't have an account? Register"
          : 'Already have an account? Login'}
      </p>
      {message && (
        <p style={{ marginTop: 12, padding: '8px 12px', borderRadius: 6,
                    background: message.includes('error') ? '#fee2e2' : '#d1fae5',
                    color:      message.includes('error') ? '#991b1b' : '#065f46',
                    fontSize: 13 }}>
          {message}
        </p>
      )}
    </div>
  )
}
