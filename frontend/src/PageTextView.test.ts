import { describe, expect, it } from 'vitest'
import { splitPageText } from './lib/pageText'

const PAGE_ONE_HEADER = `The Inner Game
of Tennis
W Timothy Gallwey
Jonathan Cape
Thirty-two Bedford Square London`

describe('splitPageText', () => {
  it('keeps imprint lines separate from body paragraphs', () => {
    const text = `${PAGE_ONE_HEADER}

Every game is composed of two parts, an outer game and an inner game.

It is the thesis of this book.`

    const { headerLines, bodyParagraphs } = splitPageText(text)
    expect(headerLines).toEqual([
      'The Inner Game',
      'of Tennis',
      'W Timothy Gallwey',
      'Jonathan Cape',
      'Thirty-two Bedford Square London',
    ])
    expect(bodyParagraphs).toHaveLength(2)
    expect(bodyParagraphs[0]).toMatch(/^Every game is composed/)
    expect(bodyParagraphs[0]).not.toContain('\n')
  })
})
