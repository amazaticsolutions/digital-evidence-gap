import { useState, useEffect } from 'react'
import { checkHealth } from './api'
import IngestPanel from './components/IngestPanel'
import QueryPanel from './components/QueryPanel'

type Tab = 'ingest' | 'query'

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'ingest', label: 'Ingest Video', icon: '📥' },
  { id: 'query', label: 'Query Evidence', icon: '🔍' },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('ingest')
  const [backendOk, setBackendOk] = useState<boolean | null>(null)

  useEffect(() => {
    checkHealth().then(setBackendOk)
    const id = setInterval(() => checkHealth().then(setBackendOk), 15_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2 mr-2">
            <span className="text-2xl">🔎</span>
            <span className="font-bold text-gray-100 text-lg tracking-tight">
              Digital Evidence Gap
            </span>
          </div>

          <nav className="flex gap-1 flex-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  tab === t.id
                    ? 'bg-brand-600 text-white'
                    : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </nav>

          {/* Backend status pill */}
          <div className="flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-gray-800">
            <span
              className={`w-2 h-2 rounded-full ${
                backendOk === null
                  ? 'bg-gray-500 animate-pulse'
                  : backendOk
                  ? 'bg-green-500'
                  : 'bg-red-500 animate-pulse'
              }`}
            />
            <span className="text-gray-400">
              {backendOk === null ? 'connecting…' : backendOk ? 'backend online' : 'backend offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Backend offline banner */}
      {backendOk === false && (
        <div className="bg-red-900/40 border-b border-red-800 px-6 py-2 text-sm text-red-300 text-center">
          ⚠️ Backend is unreachable at <code className="font-mono">http://localhost:8001</code> —
          run <code className="font-mono">python manage.py runserver 8001</code> in the{' '}
          <code className="font-mono">backend/</code> directory.
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">
        {tab === 'ingest' && <IngestPanel />}
        {tab === 'query' && <QueryPanel />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-4 text-center text-xs text-gray-600">
        Digital Evidence Gap — Multimedia RAG Demo &nbsp;·&nbsp; Django 5 + React 18 + Vite
      </footer>
    </div>
  )
}
