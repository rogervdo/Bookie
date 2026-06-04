/** Max characters per POST /api/synthesize request (backend MAX_TEXT_LENGTH). */
export const TTS_MAX_CHARS = 9000

/**
 * Split page text into chunks that fit the synthesize API limit,
 * preferring paragraph and sentence boundaries.
 */
export function chunkTextForTts(
  text: string,
  maxLen: number = TTS_MAX_CHARS,
): string[] {
  const trimmed = text.trim()
  if (!trimmed) return []
  if (trimmed.length <= maxLen) return [trimmed]

  const chunks: string[] = []
  const paragraphs = trimmed.split(/\n\n+/)

  let buffer = ''
  for (const para of paragraphs) {
    const piece = para.trim()
    if (!piece) continue

    if (piece.length > maxLen) {
      if (buffer) {
        chunks.push(buffer)
        buffer = ''
      }
      chunks.push(...splitLongPiece(piece, maxLen))
      continue
    }

    const next =
      buffer.length === 0 ? piece : `${buffer}\n\n${piece}`
    if (next.length <= maxLen) {
      buffer = next
    } else {
      chunks.push(buffer)
      buffer = piece
    }
  }

  if (buffer) chunks.push(buffer)
  return chunks
}

function splitLongPiece(text: string, maxLen: number): string[] {
  const parts: string[] = []
  let rest = text

  while (rest.length > maxLen) {
    let cut = rest.lastIndexOf('. ', 0, maxLen)
    if (cut < maxLen * 0.4) {
      cut = rest.lastIndexOf(' ', 0, maxLen)
    }
    if (cut <= 0) cut = maxLen

    const segment = rest.slice(0, cut).trim()
    if (segment) parts.push(segment)
    rest = rest.slice(cut).trim()
  }

  if (rest) parts.push(rest)
  return parts
}
