import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchHealth, synthesize } from './api'

describe('fetchHealth', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns parsed health payload', async () => {
    const payload = {
      status: 'ok',
      model_loaded: true,
      loading: false,
      load_error: null,
      device: 'cpu',
      voices: ['af_heart'],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    )

    await expect(fetchHealth()).resolves.toEqual(payload)
    expect(fetch).toHaveBeenCalledWith('/api/health')
  })

  it('throws when backend is unavailable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        text: async () => 'Service unavailable',
      }),
    )

    await expect(fetchHealth()).rejects.toThrow('Service unavailable')
  })
})

describe('synthesize', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('posts text and voice to the API', async () => {
    const blob = new Blob(['audio'], { type: 'audio/wav' })

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => blob,
      }),
    )

    await expect(synthesize('Hello', 'af_heart')).resolves.toBe(blob)
    expect(fetch).toHaveBeenCalledWith('/api/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Hello', voice: 'af_heart' }),
    })
  })

  it('throws synthesis errors from the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        text: async () => 'Kokoro is still loading',
      }),
    )

    await expect(synthesize('Hello')).rejects.toThrow('Kokoro is still loading')
  })
})
