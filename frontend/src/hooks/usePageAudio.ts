import { useCallback, useEffect, useRef, useState } from 'react'
import { synthesize } from '../api'
import { chunkTextForTts } from '../lib/ttsChunks'

export type PageAudioPhase = 'idle' | 'generating' | 'ready' | 'playing'

export function usePageAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const blobsRef = useRef<Blob[]>([])
  const urlRef = useRef<string | null>(null)
  const playIndexRef = useRef(0)

  const [phase, setPhase] = useState<PageAudioPhase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(
    null,
  )
  const [chunkCount, setChunkCount] = useState(0)

  const revokeUrl = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current)
      urlRef.current = null
    }
  }, [])

  const reset = useCallback(() => {
    audioRef.current?.pause()
    revokeUrl()
    blobsRef.current = []
    playIndexRef.current = 0
    setPhase('idle')
    setError(null)
    setProgress(null)
    setChunkCount(0)
  }, [revokeUrl])

  useEffect(() => () => reset(), [reset])

  const playBlob = useCallback((blob: Blob): Promise<void> => {
    return new Promise((resolve, reject) => {
      const audio = audioRef.current
      if (!audio) {
        reject(new Error('Audio element not ready'))
        return
      }

      revokeUrl()
      const url = URL.createObjectURL(blob)
      urlRef.current = url
      audio.src = url

      const onEnded = () => {
        cleanup()
        resolve()
      }
      const onError = () => {
        cleanup()
        reject(new Error('Playback failed'))
      }
      const cleanup = () => {
        audio.removeEventListener('ended', onEnded)
        audio.removeEventListener('error', onError)
      }

      audio.addEventListener('ended', onEnded)
      audio.addEventListener('error', onError)
      void audio.play().catch(reject)
    })
  }, [revokeUrl])

  const playAll = useCallback(async () => {
    const blobs = blobsRef.current
    if (!blobs.length) return

    setPhase('playing')
    setError(null)
    playIndexRef.current = 0

    try {
      for (let i = 0; i < blobs.length; i++) {
        playIndexRef.current = i
        await playBlob(blobs[i])
      }
      setPhase('ready')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Playback failed')
      setPhase('ready')
    }
  }, [playBlob])

  const generate = useCallback(
    async (text: string, voice: string) => {
      const chunks = chunkTextForTts(text)
      if (!chunks.length) return

      audioRef.current?.pause()
      revokeUrl()
      blobsRef.current = []
      setPhase('generating')
      setError(null)
      setProgress({ done: 0, total: chunks.length })

      try {
        const blobs: Blob[] = []
        for (let i = 0; i < chunks.length; i++) {
          blobs.push(await synthesize(chunks[i], voice))
          setProgress({ done: i + 1, total: chunks.length })
        }
        blobsRef.current = blobs
        setChunkCount(blobs.length)
        setPhase('ready')
      } catch (err) {
        blobsRef.current = []
        setChunkCount(0)
        setPhase('idle')
        setError(err instanceof Error ? err.message : 'Synthesis failed')
        setProgress(null)
      }
    },
    [revokeUrl],
  )

  const stop = useCallback(() => {
    audioRef.current?.pause()
    if (phase === 'playing') setPhase('ready')
  }, [phase])

  return {
    audioRef,
    phase,
    error,
    progress,
    chunkCount,
    generate,
    playAll,
    stop,
    reset,
    hasAudio: chunkCount > 0 && (phase === 'ready' || phase === 'playing'),
  }
}
