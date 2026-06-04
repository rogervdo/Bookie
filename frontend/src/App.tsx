import { useCallback, useEffect, useState } from 'react'
import { fetchHealth, synthesize } from './api'

const SAMPLE_TEXT =
  'The sun dipped below the horizon, painting the sky in shades of amber and violet. Somewhere in the distance, a bird called out one last time before the night settled in.'

const DEFAULT_VOICE = 'af_heart'

export default function App() {
  const [text, setText] = useState(SAMPLE_TEXT)
  const [voice, setVoice] = useState(DEFAULT_VOICE)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [health, setHealth] = useState<{
    modelLoaded: boolean
    loading: boolean
    device: string | null
    voices: string[]
    status: string
  } | null>(null)

  useEffect(() => {
    let active = true

    const poll = async () => {
      try {
        const data = await fetchHealth()
        if (!active) return
        setHealth({
          modelLoaded: data.model_loaded,
          loading: data.loading,
          device: data.device,
          voices: data.voices,
          status: data.status,
        })
        if (data.loading && !data.model_loaded) {
          window.setTimeout(poll, 2000)
        }
      } catch {
        if (!active) return
        setHealth(null)
        window.setTimeout(poll, 3000)
      }
    }

    poll()
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (health?.voices.length && !health.voices.includes(voice)) {
      setVoice(health.voices[0])
    }
  }, [health, voice])

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl)
    }
  }, [audioUrl])

  const handleRead = useCallback(async () => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }

    try {
      const blob = await synthesize(trimmed, voice)
      const url = URL.createObjectURL(blob)
      setAudioUrl(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [text, loading, audioUrl, voice])

  const voices = health?.voices ?? []
  const modelReady = health?.modelLoaded ?? false
  const canRead = text.trim().length > 0 && !loading && modelReady

  return (
    <div className="min-h-svh bg-[#0f1419] text-gray-100 flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Speaking
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Local text-to-speech powered by Kokoro
          </p>
          {health && (
            <p className="mt-1 text-xs text-gray-500">
              {health.modelLoaded
                ? `Ready · ${health.device}`
                : 'Loading model… first run may take a minute'}
            </p>
          )}
          {!health && (
            <p className="mt-1 text-xs text-red-400">Backend offline</p>
          )}
        </header>

        <div className="rounded-2xl border border-gray-800 bg-[#161b22] p-6 shadow-xl">
          {voices.length > 0 && (
            <div className="mb-4">
              <label
                htmlFor="voice-select"
                className="mb-1.5 block text-sm text-gray-400"
              >
                Voice
              </label>
              <select
                id="voice-select"
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                className="w-full rounded-xl border border-gray-700 bg-[#0f1419] px-3 py-2.5 text-sm text-gray-100 focus:border-amber-500/60 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
              >
                {voices.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          )}

          <label htmlFor="text-input" className="sr-only">
            Text to read aloud
          </label>
          <textarea
            id="text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            maxLength={500}
            placeholder="Enter text to read aloud…"
            className="w-full resize-none rounded-xl border border-gray-700 bg-[#0f1419] px-4 py-3 text-base leading-relaxed text-gray-100 placeholder:text-gray-600 focus:border-amber-500/60 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
          />

          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <span>{text.length} / 500</span>
            {!modelReady && health && (
              <span className="text-amber-400/80">Waiting for model…</span>
            )}
          </div>

          {error && (
            <div
              role="alert"
              className="mt-4 rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-300"
            >
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleRead}
            disabled={!canRead}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-amber-600 px-6 py-3 text-base font-medium text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Generating…
              </>
            ) : (
              'Read'
            )}
          </button>

          {audioUrl && (
            <div className="mt-6 rounded-xl border border-gray-700 bg-[#0f1419] p-4">
              <p className="mb-3 text-sm text-gray-400">Playback · {voice}</p>
              <audio src={audioUrl} controls autoPlay className="w-full" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
