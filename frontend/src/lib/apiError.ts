export async function readApiError(res: Response, fallback: string): Promise<string> {
  const text = await res.text()
  if (!text) return fallback
  try {
    const data = JSON.parse(text) as { detail?: string | { msg?: string }[] }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg
    }
  } catch {
    // not JSON
  }
  return text
}
