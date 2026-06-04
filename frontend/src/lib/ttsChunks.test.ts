import { describe, expect, it } from 'vitest'
import { chunkTextForTts, TTS_MAX_CHARS } from './ttsChunks'

describe('chunkTextForTts', () => {
  it('returns empty for blank input', () => {
    expect(chunkTextForTts('   ')).toEqual([])
  })

  it('returns single chunk when under limit', () => {
    expect(chunkTextForTts('Hello world.')).toEqual(['Hello world.'])
  })

  it('splits on paragraph boundaries', () => {
    const a = 'A'.repeat(200)
    const b = 'B'.repeat(200)
    const chunks = chunkTextForTts(`${a}\n\n${b}`, 250)
    expect(chunks).toHaveLength(2)
    expect(chunks[0]).toBe(a)
    expect(chunks[1]).toBe(b)
  })

  it('keeps every chunk within max length', () => {
    const long = 'Word. '.repeat(2000)
    const chunks = chunkTextForTts(long, TTS_MAX_CHARS)
    expect(chunks.length).toBeGreaterThan(1)
    for (const chunk of chunks) {
      expect(chunk.length).toBeLessThanOrEqual(TTS_MAX_CHARS)
    }
  })
})
