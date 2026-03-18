/**
 * ScanProgress.tsx — live streaming progress display for Smart Scan.
 */
import type { ReactNode } from 'react'

export interface ProgressUpdate {
  type: string
  step?: string
  current?: number
  total?: number
  ticker?: string
  message?: string
  pct?: number
}

const STEP_LABELS: Record<string, string> = {
  news: 'Fetching news',
  financials: 'Loading financials',
  scoring: 'Scoring signals',
}

export default function ScanProgress({
  progress,
  warningsCount,
}: {
  progress: ProgressUpdate | null
  warningsCount: number
}): ReactNode {
  if (!progress) return null

  const pct = progress.pct || 0
  const stepLabel = STEP_LABELS[progress.step || ''] || 'Processing'

  return (
    <div style={{
      margin: '0 18px 16px',
      padding: '14px 16px',
      background: '#f8faff',
      border: '1px solid #bfdbfe',
      borderRadius: 8,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: 8,
        fontSize: 13,
      }}>
        <span style={{ fontWeight: 500, color: '#1e40af' }}>
          {stepLabel}
        </span>
        <span style={{ color: '#6b7280' }}>
          {progress.current || 0} / {progress.total || 0}
        </span>
      </div>

      <div style={{
        height: 8,
        background: '#dbeafe',
        borderRadius: 4,
        overflow: 'hidden',
        marginBottom: 8,
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: '#2563eb',
          borderRadius: 4,
          transition: 'width 0.3s ease',
        }} />
      </div>

      <div style={{ fontSize: 12, color: '#374151' }}>
        {progress.message || 'Processing...'}
        {warningsCount > 0 && (
          <span style={{ color: '#ca8a04', marginLeft: 8 }}>
            ({warningsCount} warnings)
          </span>
        )}
      </div>
    </div>
  )
}

