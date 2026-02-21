import type {
  IngestPayload,
  IngestResponse,
  QueryPayload,
  QueryResponse,
} from './types'

const BASE = '/api'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) {
    const msg = data?.error ?? data?.detail ?? data?.message ?? `HTTP ${res.status}`
    throw new Error(msg)
  }
  if (data?.error) {
    // Backend returned 200 but with an error field (shouldn't happen, but guard it)
    throw new Error(data.error)
  }
  return data as T
}

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error ?? `HTTP ${res.status}`)
  return data as T
}

/** Ingest a Google Drive video — triggers the full RAG pipeline */
export function ingestVideo(payload: IngestPayload): Promise<IngestResponse> {
  return post<IngestResponse>('/evidence/ingest/', payload)
}

/** Run a natural-language forensic query against ingested evidence */
export function runQuery(payload: QueryPayload): Promise<QueryResponse> {
  return post<QueryResponse>('/search/query/', payload)
}

/**
 * Build the backend proxy URL for streaming a Google Drive video.
 * The backend endpoint: GET /api/evidence/video-proxy/?video_url=<gdrive_url>
 */
export function videoProxyUrl(gdriveUrl: string, startSeconds = 0): string {
  const params = new URLSearchParams({ video_url: gdriveUrl })
  if (startSeconds > 0) params.set('start', String(Math.floor(startSeconds)))
  return `${BASE}/evidence/video-proxy/?${params.toString()}`
}

/** Simple health check — returns true if the backend is reachable */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health/`, { method: 'GET' })
    return res.ok
  } catch {
    return false
  }
}
