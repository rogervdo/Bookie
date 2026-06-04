export interface HealthStatus {
  status: string
  model_loaded: boolean
  loading: boolean
  load_error: string | null
  device: string | null
  voices: string[]
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch('/api/health')
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || 'Backend unavailable')
  }
  return res.json()
}

export async function synthesize(text: string, voice?: string): Promise<Blob> {
  const res = await fetch('/api/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice }),
  })

  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || 'Synthesis failed')
  }

  return res.blob()
}
