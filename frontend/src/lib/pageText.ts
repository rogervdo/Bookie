/** Split stored page text into imprint lines and body paragraphs. */

export interface PageTextSections {
  headerLines: string[]
  bodyParagraphs: string[]
}

export function splitPageText(text: string): PageTextSections {
  const trimmed = text.trim()
  if (!trimmed) {
    return { headerLines: [], bodyParagraphs: [] }
  }

  const splitAt = trimmed.indexOf('\n\n')
  if (splitAt < 0) {
    return { headerLines: [], bodyParagraphs: [trimmed] }
  }

  const header = trimmed.slice(0, splitAt)
  const body = trimmed.slice(splitAt + 2).trim()

  return {
    headerLines: header.split('\n').filter(Boolean),
    bodyParagraphs: body ? body.split(/\n\n+/).filter(Boolean) : [],
  }
}
