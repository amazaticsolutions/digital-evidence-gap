// ---- Ingest ---------------------------------------------------------------

export interface IngestPayload {
  gdrive_url: string
  cam_id: string
  gps_lat: number
  gps_lng: number
  skip_existing?: boolean
}

/** Matches POST /api/evidence/ingest/ response */
export interface IngestResponse {
  /** Number of frames ingested into MongoDB */
  frames_ingested: number
  cam_id: string
  /** Present when the request fails */
  error?: string
}

// ---- Search / Query -------------------------------------------------------

export interface QueryPayload {
  query: string
  include_images?: boolean
  top_k?: number
}

/**
 * One frame result as returned by format_results_for_display().
 * score is 0–100 (LLM relevance rating, threshold = 40).
 */
export interface FrameResult {
  /** MongoDB document _id */
  _id?: string
  cam_id?: string
  /** Seconds from video start */
  timestamp?: number
  /** LLM relevance score 0–100 */
  score: number
  relevant?: boolean
  explanation?: string
  caption_brief?: string
  caption_detailed?: string
  /** Original Google Drive share URL */
  gdrive_url?: string
  gps_lat?: number
  gps_lng?: number
  reid_group?: string
  sequence?: number
  /** base64-encoded JPEG (only present when include_images=true) */
  image_base64?: string
}

/** Matches POST /api/search/query/ response */
export interface QueryResponse {
  query: string
  total_searched: number
  total_found: number
  results: FrameResult[]
  timeline: FrameResult[]
  search_method: string
  queries_used: string[]
  /** LLM-generated finding summary */
  summary: string
  /** Present when the request fails */
  error?: string
}
