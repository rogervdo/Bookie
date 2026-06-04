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
