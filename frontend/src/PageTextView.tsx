import { splitPageText } from './lib/pageText'

interface PageTextViewProps {
  text: string
  variant?: 'library' | 'reader'
}

export default function PageTextView({
  text,
  variant = 'library',
}: PageTextViewProps) {
  const { headerLines, bodyParagraphs } = splitPageText(text)
  const isReader = variant === 'reader'

  return (
    <div
      className={
        isReader
          ? 'px-2 py-2 sm:px-4 sm:py-4'
          : 'rounded-xl border border-gray-700 bg-[#0f1419] p-4'
      }
    >
      {headerLines.length > 0 && (
        <div
          className={
            isReader
              ? 'mb-8 space-y-1 border-b border-stone-300/80 pb-6 text-center'
              : 'mb-6 space-y-1 border-b border-gray-700 pb-4'
          }
        >
          {headerLines.map((line, i) => (
            <p
              key={line}
              className={
                isReader
                  ? `${i === 0 ? 'font-serif text-2xl font-medium tracking-tight text-stone-900' : 'text-sm text-stone-600'}`
                  : 'text-sm text-gray-300'
              }
            >
              {line}
            </p>
          ))}
        </div>
      )}
      {bodyParagraphs.map((paragraph) => (
        <p
          key={paragraph.slice(0, 48)}
          className={
            isReader
              ? 'mb-5 font-serif text-[1.05rem] leading-[1.75] text-stone-800 last:mb-0 sm:text-lg sm:leading-[1.8]'
              : 'mb-4 text-sm leading-relaxed text-gray-200 last:mb-0'
          }
        >
          {paragraph}
        </p>
      ))}
    </div>
  )
}
