import { useState } from 'react'
import LibraryTab from './LibraryTab'
import ReadTab from './ReadTab'
import TestTab from './TestTab'
import { useHealth } from './useHealth'

type TabId = 'test' | 'library' | 'read'

const TABS: { id: TabId; label: string }[] = [
  { id: 'test', label: 'Test' },
  { id: 'library', label: 'Library' },
  { id: 'read', label: 'Read' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('test')
  const health = useHealth()
  const isRead = activeTab === 'read'

  return (
    <div className="min-h-svh bg-[#0f1419] text-gray-100 flex items-center justify-center p-6">
      <div className={`w-full ${isRead ? 'max-w-4xl' : 'max-w-2xl'}`}>
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

        <nav className="mb-4 flex gap-2 rounded-xl border border-gray-800 bg-[#161b22] p-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition ${
                activeTab === tab.id
                  ? 'bg-amber-600 text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {activeTab === 'test' && <TestTab health={health} />}
        {activeTab === 'library' && <LibraryTab />}
        {activeTab === 'read' && <ReadTab health={health} />}
      </div>
    </div>
  )
}
