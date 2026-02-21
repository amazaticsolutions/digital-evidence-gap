import { useState } from 'react'
import { runQuery } from '../api'
import type { QueryPayload, QueryResponse } from '../types'
import ResultCard from './ResultCard'

type Stage = 'idle' | 'loading' | 'done' | 'error'

export default function QueryPanel() {
  const [queryText, setQueryText] = useState('')
  const [includeImages, setIncludeImages] = useState(true)
  const [stage, setStage] = useState<Stage>('idle')
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!queryText.trim()) return
    setStage('loading')
    setResponse(null)
    setErrorMsg('')
    try {
      const payload: QueryPayload = {
        query: queryText.trim(),
        include_images: includeImages,
      }
      const res = await runQuery(payload)
      setResponse(res)
      setStage('done')
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err))
      setStage('error')
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-xl font-semibold text-gray-100">Query Evidence</h2>

      <p className="text-sm text-gray-400">
        Ask a natural-language question about the ingested footage. The RAG
        pipeline will retrieve relevant frames, score them with an LLM, and
        present matched clips you can play inline.
      </p>

      <form onSubmit={handleSearch} className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 rounded-lg bg-gray-800 border border-gray-700 px-3 py-2.5
                       text-sm text-gray-100 placeholder-gray-500 focus:outline-none
                       focus:ring-2 focus:ring-brand-500"
            placeholder='e.g. "red backpack dropped near the entrance at night"'
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
          />
          <button
            type="submit"
            disabled={stage === 'loading'}
            className="rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50
                       px-5 py-2.5 text-sm font-semibold text-white transition-colors whitespace-nowrap"
          >
            {stage === 'loading' ? '⏳ Searching…' : '🔍 Search'}
          </button>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            className="accent-brand-500"
            checked={includeImages}
            onChange={(e) => setIncludeImages(e.target.checked)}
          />
          Include frame thumbnails in results
        </label>
      </form>

      {/* LLM finding summary */}
      {response?.summary && (
        <div className="rounded-xl border border-brand-700 bg-brand-900/20 p-4">
          <p className="text-xs font-semibold text-brand-400 mb-2 uppercase tracking-wide">
            🤖 AI Findings Summary
          </p>
          <p className="text-sm text-gray-200 leading-relaxed">{response.summary}</p>
        </div>
      )}

      {/* Stats row */}
      {stage === 'done' && response && (
        <div className="flex gap-4 text-xs text-gray-500">
          <span>Frames searched: <strong className="text-gray-300">{response.total_searched}</strong></span>
          <span>Relevant found: <strong className="text-gray-300">{response.total_found}</strong></span>
          <span>Method: <strong className="text-gray-300">{response.search_method}</strong></span>
        </div>
      )}

      {/* Error */}
      {stage === 'error' && (
        <div className="rounded-xl border border-red-700 bg-red-900/20 p-4 text-sm text-red-300">
          ❌ {errorMsg}
        </div>
      )}

      {/* Results */}
      {stage === 'done' && response && (
        <div className="space-y-4">
          {response.results.length === 0 ? (
            <p className="text-gray-500 text-sm">
              No matching frames found. Try a more specific query mentioning an object, person, action, or time.
            </p>
          ) : (
            response.results.map((r, i) => (
              <ResultCard key={r._id ?? i} result={r} rank={i + 1} />
            ))
          )}
        </div>
      )}
    </div>
  )
}
