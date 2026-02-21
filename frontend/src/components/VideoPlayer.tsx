import { useEffect, useRef } from 'react'
import { videoProxyUrl } from '../api'

interface Props {
  /** Google Drive share URL from the FrameResult.gdrive_url field */
  gdriveUrl: string
  startSeconds?: number
}

export default function VideoPlayer({ gdriveUrl, startSeconds = 0 }: Props) {
  const ref = useRef<HTMLVideoElement>(null)
  const src = videoProxyUrl(gdriveUrl, startSeconds)

  // Reload the video element whenever the source URL changes
  useEffect(() => {
    if (ref.current) ref.current.load()
  }, [src])

  return (
    <div className="rounded-xl overflow-hidden bg-black border border-gray-700 mt-3">
      <video
        ref={ref}
        controls
        className="w-full max-h-80"
        onLoadedMetadata={() => {
          // Seek to the exact frame timestamp once metadata is available
          if (ref.current && startSeconds > 0) {
            ref.current.currentTime = startSeconds
          }
        }}
      >
        {/*
         * The backend /api/evidence/video-proxy/ endpoint streams the Drive
         * file with byte-range support so the browser can seek freely.
         */}
        <source src={src} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      {startSeconds > 0 && (
        <div className="bg-gray-900 px-3 py-1 text-xs text-gray-400">
          Starts at {Math.floor(startSeconds / 60)}:{String(Math.floor(startSeconds % 60)).padStart(2, '0')}
        </div>
      )}
    </div>
  )
}
