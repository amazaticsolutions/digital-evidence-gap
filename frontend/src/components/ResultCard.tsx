import { useState } from 'react'
import type { FrameResult } from '../types'
import VideoPlayer from './VideoPlayer'

interface Props {
  result: FrameResult
  rank: number
}

function formatTime(secs?: number): string {
  if (secs === undefined) return '—'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

/** Score is 0–100 from the LLM; map to a colour band. */
function scoreBadgeCls(score: number): string {
  if (score >= 80) return 'bg-green-900 text-green-300'
  if (score >= 50) return 'bg-yellow-900 text-yellow-300'
  return 'bg-gray-800 text-gray-400'
}

export default function ResultCard({ result, rank }: Props) {
  const [showVideo, setShowVideo] = useState(false)

  // Build thumbnail src from base64 if present
  const thumbnailSrc = result.image_base64
    ? `data:image/jpeg;base64,${result.image_base64}`
    : undefined

  const label = result.cam_id ?? result._id ?? `Frame ${rank}`

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-900 p-4 space-y-3">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold text-gray-500">#{rank}</span>
          <span className="text-sm font-semibold text-gray-100">{label}</span>
          {result.timestamp !== undefined && (
            <span className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded-full">
              ⏱ {formatTime(result.timestamp)}
            </span>
          )}
          {result.gps_lat !== undefined && result.gps_lng !== undefined && (
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
              📍 {result.gps_lat.toFixed(4)}, {result.gps_lng.toFixed(4)}
            </span>
          )}
        </div>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${scoreBadgeCls(result.score)}`}>
          {result.score}/100
        </span>
      </div>

      {/* Thumbnail + caption */}
      <div className="flex gap-3">
        {thumbnailSrc && (
          <img
            src={thumbnailSrc}
            alt={`Frame from ${label}`}
            className="w-32 h-20 object-cover rounded-lg border border-gray-700 flex-shrink-0"
          />
        )}
        <div className="space-y-1 min-w-0">
          {result.explanation && (
            <p className="text-sm text-gray-200 leading-relaxed">{result.explanation}</p>
          )}
          {result.caption_brief && (
            <p className="text-xs text-gray-400 italic">{result.caption_brief}</p>
          )}
        </div>
      </div>

      {/* Watch at timestamp */}
      {result.gdrive_url && (
        <>
          <button
            onClick={() => setShowVideo((v) => !v)}
            className="text-xs font-medium text-brand-400 hover:text-brand-300 transition-colors"
          >
            {showVideo ? '▲ Hide video' : '▶ Watch at timestamp'}
          </button>
          {showVideo && (
            <VideoPlayer gdriveUrl={result.gdrive_url} startSeconds={result.timestamp ?? 0} />
          )}
        </>
      )}
    </div>
  )
}
