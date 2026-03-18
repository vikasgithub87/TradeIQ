/**
 * ScanPanel.tsx — Smart Scan Control Panel.
 * Inline section above ScoresPanel on the dashboard.
 */
import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import ScanProgress, { type ProgressUpdate } from './ScanProgress'

const API_URL = import.meta.env.VITE_API_URL as string

interface CategoryMeta {
  label: string
  icon: string
  description: string
  color: string
  type: string
}

const COUNT_OPTIONS = [10, 20, 30, 50]

interface Props {
  onScanComplete?: () => void
}

export default function ScanPanel({ onScanComplete }: Props) {
  const [categories, setCategories] = useState<Record<string, CategoryMeta>>({})
  const [selected, setSelected] = useState<string>('nifty50')
  const [count, setCount] = useState<number>(20)
  const [running, setRunning] = useState<boolean>(false)
  const [progress, setProgress] = useState<ProgressUpdate | null>(null)
  const [completed, setCompleted] = useState<any | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [saveDefault, setSaveDefault] = useState<boolean>(false)
  const [showPreview, setShowPreview] = useState<boolean>(false)
  const [previewList, setPreviewList] = useState<any[]>([])
  const [savedDefault, setSavedDefault] = useState<string>('nifty50')
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!API_URL || API_URL === 'undefined') return

    axios.get(`${API_URL}/scan/categories`)
      .then(res => setCategories(res.data.categories || {}))
      .catch(() => setCategories({}))

    axios.get(`${API_URL}/scan/profile`)
      .then(res => {
        const p = res.data || {}
        setSelected(p.last_category || 'nifty50')
        setCount(p.last_count || 20)
        setSavedDefault(p.default_category || 'nifty50')
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!showPreview) return
    if (!API_URL || API_URL === 'undefined') return
    axios.get(`${API_URL}/scan/preview/${selected}?count=${count}`)
      .then(res => setPreviewList(res.data.companies || []))
      .catch(() => setPreviewList([]))
  }, [selected, count, showPreview])

  const runScan = async () => {
    if (!API_URL || API_URL === 'undefined') return
    setRunning(true)
    setProgress(null)
    setCompleted(null)
    setWarnings([])

    abortRef.current = new AbortController()

    try {
      const response = await fetch(`${API_URL}/scan/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: selected,
          count,
          save_as_default: saveDefault,
        }),
        signal: abortRef.current.signal,
      })

      if (!response.ok || !response.body) {
        setProgress({ type: 'error', message: 'Scan failed to start' } as any)
        setRunning(false)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const update: any = JSON.parse(line.slice(6))
            if (update.type === 'progress' || update.type === 'start') {
              setProgress(update)
            } else if (update.type === 'warning') {
              setWarnings(w => [...w, `${update.ticker}: ${update.message}`])
            } else if (update.type === 'complete') {
              setCompleted(update)
              setProgress(null)
              setRunning(false)
              if (saveDefault) setSavedDefault(selected)
              onScanComplete?.()
            } else if (update.type === 'error') {
              setProgress({ type: 'error', message: update.message } as any)
              setRunning(false)
            }
          } catch {}
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setProgress({ type: 'error', message: 'Connection failed' } as any)
      }
      setRunning(false)
    }
  }

  const stopScan = () => {
    abortRef.current?.abort()
    setRunning(false)
    setProgress(null)
  }

  const cat = categories[selected]
  const catColor = cat?.color || '#2563eb'

  return (
    <div style={{
      border: '1px solid #e5e7eb',
      borderRadius: 12,
      overflow: 'hidden',
      marginBottom: 24,
      background: '#fff',
    }}>
      <div style={{
        padding: '14px 18px',
        borderBottom: '1px solid #f3f4f6',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#fafafa',
      }}>
        <div>
          <span style={{ fontSize: 15, fontWeight: 600 }}>
            Smart Scan
          </span>
          <span style={{
            fontSize: 11,
            marginLeft: 8,
            background: '#f0fdf4',
            color: '#16a34a',
            padding: '2px 8px',
            borderRadius: 10,
          }}>
            No Redis needed
          </span>
        </div>
        {savedDefault && (
          <span style={{ fontSize: 12, color: '#6b7280' }}>
            Default: <strong>{categories[savedDefault]?.label || savedDefault}</strong>
          </span>
        )}
      </div>

      <div style={{ padding: '16px 18px' }}>
        <div style={{ marginBottom: 14 }}>
          <label style={{
            fontSize: 12,
            fontWeight: 500,
            color: '#374151',
            display: 'block',
            marginBottom: 8,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            Scan Category
          </label>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
            gap: 8,
          }}>
            {Object.entries(categories).map(([key, meta]) => {
              const isSelected = selected === key
              const isDefault = savedDefault === key
              return (
                <div
                  key={key}
                  onClick={() => !running && setSelected(key)}
                  style={{
                    border: isSelected ? `2px solid ${meta.color}` : '1px solid #e5e7eb',
                    borderRadius: 8,
                    padding: '10px 12px',
                    cursor: running ? 'not-allowed' : 'pointer',
                    background: isSelected ? meta.color + '12' : '#fff',
                    position: 'relative',
                    transition: 'all 0.15s ease',
                    opacity: running ? 0.6 : 1,
                  }}
                >
                  {isDefault && (
                    <div style={{
                      position: 'absolute',
                      top: -1,
                      right: 6,
                      fontSize: 9,
                      fontWeight: 600,
                      color: meta.color,
                      background: '#fff',
                      padding: '0 4px',
                      borderRadius: 3,
                    }}>
                      DEFAULT
                    </div>
                  )}
                  <div style={{
                    fontSize: 13,
                    fontWeight: isSelected ? 600 : 500,
                    color: isSelected ? meta.color : '#374151',
                    marginBottom: 3,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}>
                    <span style={{ fontSize: 12 }}>{meta.icon}</span>
                    {meta.label}
                  </div>
                  <div style={{
                    fontSize: 11,
                    color: '#9ca3af',
                    lineHeight: 1.3,
                  }}>
                    {meta.description}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          flexWrap: 'wrap',
          marginBottom: 14,
        }}>
          <div>
            <label style={{
              fontSize: 12,
              fontWeight: 500,
              color: '#374151',
              display: 'block',
              marginBottom: 6,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}>
              Companies
            </label>
            <div style={{ display: 'flex', gap: 6 }}>
              {COUNT_OPTIONS.map(n => (
                <button
                  key={n}
                  onClick={() => !running && setCount(n)}
                  disabled={running}
                  style={{
                    padding: '6px 14px',
                    fontSize: 13,
                    fontWeight: count === n ? 600 : 400,
                    border: count === n ? `2px solid ${catColor}` : '1px solid #e5e7eb',
                    borderRadius: 6,
                    background: count === n ? catColor + '12' : '#fff',
                    color: count === n ? catColor : '#374151',
                    cursor: running ? 'not-allowed' : 'pointer',
                  }}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginLeft: 'auto' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              color: '#6b7280',
              cursor: 'pointer',
            }}>
              <input
                type="checkbox"
                checked={saveDefault}
                onChange={e => setSaveDefault(e.target.checked)}
                disabled={running}
              />
              Save as default
            </label>

            <button
              onClick={() => setShowPreview(!showPreview)}
              disabled={running}
              style={{
                padding: '5px 12px',
                fontSize: 12,
                border: '1px solid #e5e7eb',
                borderRadius: 6,
                background: '#fff',
                color: '#374151',
                cursor: 'pointer',
              }}
            >
              {showPreview ? 'Hide preview' : 'Preview companies'}
            </button>
          </div>
        </div>

        {showPreview && previewList.length > 0 && (
          <div style={{
            marginBottom: 14,
            padding: '10px 14px',
            background: '#f9fafb',
            borderRadius: 8,
            border: '1px solid #e5e7eb',
          }}>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#374151', marginBottom: 8 }}>
              {previewList.length} companies will be scanned:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {previewList.map((c: any) => (
                <span key={c.ticker} style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: 10,
                  color: '#374151',
                }}>
                  {c.ticker}
                </span>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={running ? stopScan : runScan}
            style={{
              flex: 1,
              padding: '11px 20px',
              fontSize: 14,
              fontWeight: 600,
              border: 'none',
              borderRadius: 8,
              background: running ? '#dc2626' : catColor,
              color: '#fff',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            {running ? 'Stop Scan' : `Scan ${count} ${cat?.label || selected} Companies`}
          </button>
        </div>
      </div>

      {(running || progress) && progress?.type !== 'error' && (
        <ScanProgress progress={progress} warningsCount={warnings.length} />
      )}

      {progress?.type === 'error' && (
        <div style={{
          margin: '0 18px 16px',
          padding: '10px 14px',
          background: '#fef2f2',
          border: '1px solid #fca5a5',
          borderRadius: 8,
          fontSize: 13,
          color: '#991b1b',
        }}>
          Error: {(progress as any).message}
        </div>
      )}

      {completed && (
        <div style={{
          margin: '0 18px 16px',
          padding: '12px 16px',
          background: '#f0fdf4',
          border: '1px solid #86efac',
          borderRadius: 8,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#15803d', marginBottom: 6 }}>
            ✓ {completed.message}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div style={{
          margin: '0 18px 16px',
          padding: '8px 12px',
          background: '#fffbeb',
          border: '1px solid #fde68a',
          borderRadius: 8,
          fontSize: 11,
          color: '#92400e',
        }}>
          {warnings.length} warning(s) — some companies had data issues
        </div>
      )}
    </div>
  )
}

