import { useState } from 'react'
import { ingestVideo } from '../api'
import type { IngestPayload, IngestResponse } from '../types'

type Stage = 'idle' | 'loading' | 'success' | 'error'

const defaultForm: IngestPayload = {
  gdrive_url: '',
  cam_id: '',
  gps_lat: 0,
  gps_lng: 0,
  skip_existing: true,
}

export default function IngestPanel() {
  const [form, setForm] = useState<IngestPayload>(defaultForm)
  const [stage, setStage] = useState<Stage>('idle')
  const [log, setLog] = useState<string[]>([])
  const [result, setResult] = useState<IngestResponse | null>(null)

  function addLog(msg: string) {
    setLog((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`])
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.gdrive_url.trim()) return
    setStage('loading')
    setLog([])
    setResult(null)
    addLog('Submitting ingest request to backend…')
    addLog(`URL  : ${form.gdrive_url}`)
    addLog(`Cam  : ${form.cam_id || '(none)'}   GPS: ${form.gps_lat}, ${form.gps_lng}`)
    try {
      const res = await ingestVideo(form)
      setResult(res)
      addLog(`✅ Ingestion complete — ${res.frames_ingested} frame(s) stored for camera ${res.cam_id}`)
      setStage('success')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      addLog(`❌ Error: ${msg}`)
      setStage('error')
    }
  }

  const inputCls =
    'w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-gray-100 ' +
    'placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500'

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-xl font-semibold text-gray-100">Ingest Video Evidence</h2>

      <p className="text-sm text-gray-400">
        Paste a Google Drive share link below. The backend will download the video,
        extract frames, generate captions &amp; embeddings, and store everything in MongoDB.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Google Drive URL *</label>
          <input
            type="url"
            className={inputCls}
            placeholder="https://drive.google.com/file/d/FILE_ID/view?usp=sharing"
            value={form.gdrive_url}
            onChange={(e) => setForm({ ...form, gdrive_url: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Camera ID *</label>
          <input
            type="text"
            className={inputCls}
            placeholder="CAM-01"
            value={form.cam_id}
            onChange={(e) => setForm({ ...form, cam_id: e.target.value })}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">GPS Latitude</label>
            <input
              type="number"
              step="any"
              className={inputCls}
              placeholder="51.5074"
              value={form.gps_lat || ''}
              onChange={(e) => setForm({ ...form, gps_lat: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">GPS Longitude</label>
            <input
              type="number"
              step="any"
              className={inputCls}
              placeholder="-0.1278"
              value={form.gps_lng || ''}
              onChange={(e) => setForm({ ...form, gps_lng: parseFloat(e.target.value) || 0 })}
            />
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            className="accent-brand-500"
            checked={form.skip_existing}
            onChange={(e) => setForm({ ...form, skip_existing: e.target.checked })}
          />
          Skip already-ingested frames
        </label>

        <button
          type="submit"
          disabled={stage === 'loading'}
          className="w-full rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-50
                     px-4 py-2.5 text-sm font-semibold text-white transition-colors"
        >
          {stage === 'loading' ? '⏳ Processing (this can take several minutes)…' : '📥 Ingest Video'}
        </button>
      </form>

      {/* Live log console */}
      {log.length > 0 && (
        <div className="rounded-lg bg-gray-900 border border-gray-700 p-4 font-mono text-xs space-y-1 max-h-64 overflow-y-auto">
          {log.map((line, i) => (
            <p
              key={i}
              className={
                line.includes('❌')
                  ? 'text-red-400'
                  : line.includes('✅')
                  ? 'text-green-400'
                  : 'text-gray-300'
              }
            >
              {line}
            </p>
          ))}
          {stage === 'loading' && (
            <p className="text-brand-400 animate-pulse">
              ⏳ Running pipeline — frame extraction → captioning → embedding → MongoDB…
            </p>
          )}
        </div>
      )}

      {/* Success summary */}
      {stage === 'success' && result && (
        <div className="rounded-lg border border-green-700 bg-green-900/20 p-4 space-y-1">
          <p className="font-semibold text-green-400">✅ Ingest complete</p>
          <p className="text-sm text-gray-300">
            Camera: <span className="font-mono text-gray-100">{result.cam_id}</span>
          </p>
          <p className="text-sm text-gray-300">
            Frames stored:{' '}
            <span className="font-mono text-gray-100">{result.frames_ingested}</span>
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Switch to the <strong className="text-gray-200">Query Evidence</strong> tab to search this footage.
          </p>
        </div>
      )}
    </div>
  )
}
