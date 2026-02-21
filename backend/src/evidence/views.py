"""
Evidence views — video proxy/stream and video ingestion endpoints.

Endpoints:
    GET  /api/evidence/video-proxy/?video_url=<url_or_id>&start=<seconds>
    POST /api/evidence/ingest/
         Body: {"gdrive_url": str, "cam_id": str, "gps_lat": float, "gps_lng": float}

The proxy view streams video bytes from Google Drive (or a local temp file)
supporting HTTP Range requests for seek-capable players.

The ingest view downloads the video, extracts frames, generates captions &
embeddings using Florence-2, and stores everything in MongoDB.
"""

import io
import json
import logging
import os
import re
from typing import Iterator

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    StreamingHttpResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from multimedia_rag import config
from multimedia_rag.drive.gdrive import _extract_file_id, _get_drive_service
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB streaming chunks


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _stream_drive_file(file_id: str) -> Iterator[bytes]:
    """Stream a Google Drive file via MediaIoBaseDownload in 1 MB chunks."""
    service = _get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _status, done = downloader.next_chunk(num_retries=3)
        fh.seek(0)
        chunk = fh.read()
        if chunk:
            yield chunk
        fh.truncate(0)
        fh.seek(0)


# ---------------------------------------------------------------------------
# Video proxy view
# ---------------------------------------------------------------------------

@require_GET
def video_proxy(request):
    """Proxy a video to the client.

    Query params:
        - video_url: Google Drive URL or file ID OR local file path under TMP dir
        - start: optional float seconds (frontend should seek after load)
    """
    video_url = request.GET.get('video_url')
    if not video_url:
        return HttpResponseBadRequest('Missing video_url parameter')

    # If the caller passed a local path inside TEMP_VIDEO_DIR, stream file directly
    try:
        # Normalise and check if it's a path within TEMP_VIDEO_DIR
        if os.path.isabs(video_url) and os.path.commonpath([video_url, config.TEMP_VIDEO_DIR]) == os.path.abspath(config.TEMP_VIDEO_DIR) and os.path.exists(video_url):
            def file_iterator(path, chunk_size=CHUNK_SIZE):
                with open(path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk

            # Support Range header for local files
            range_header = request.headers.get('Range') or request.META.get('HTTP_RANGE')
            file_size = os.path.getsize(video_url)

            def local_stream(start: int, end: int) -> Iterator[bytes]:
                with open(video_url, 'rb') as f:
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = f.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            if range_header:
                m = re.match(r'bytes=(\d+)-(\d+)?', range_header)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    resp = StreamingHttpResponse(local_stream(start, end), status=206, content_type='video/mp4')
                    resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                    resp['Content-Length'] = str(end - start + 1)
                    resp['Accept-Ranges'] = 'bytes'
                    return resp

            resp = StreamingHttpResponse(file_iterator(video_url), content_type='video/mp4')
            resp['Content-Disposition'] = 'inline; filename="video.mp4"'
            resp['Accept-Ranges'] = 'bytes'
            resp['Content-Length'] = str(file_size)
            return resp
    except Exception:
        # Fall through to treating as Drive URL/ID
        pass

    # Otherwise treat as a Google Drive URL or file id
    try:
        file_id = _extract_file_id(video_url)
    except Exception as e:
        return HttpResponseBadRequest(f'Invalid video_url or file id: {e}')

    # Attempt to honour Range header when proxying from Google Drive
    range_header = request.headers.get('Range') or request.META.get('HTTP_RANGE')
    try:
        service = _get_drive_service()
        if range_header and hasattr(service, '_http'):
            # Use the underlying HTTP client to request a byte range
            url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
            headers = {'Range': range_header}
            try:
                resp_http, content = service._http.request(uri=url, method='GET', headers=headers)
            except Exception:
                resp_http, content = None, None

            if resp_http and content is not None:
                status = int(getattr(resp_http, 'status', 200))
                django_status = 206 if status == 206 else 200
                # If server returned Content-Range, forward it; otherwise craft a simple one
                content_range = resp_http.get('content-range') or resp_http.get('Content-Range')
                stream = iter([content])
                resp = StreamingHttpResponse(stream, status=django_status, content_type='video/mp4')
                if content_range:
                    resp['Content-Range'] = content_range
                resp['Accept-Ranges'] = 'bytes'
                resp['Content-Length'] = str(len(content))
                return resp

        # Fallback to full-stream download using the MediaIoBaseDownload
        stream = _stream_drive_file(file_id)
        resp = StreamingHttpResponse(stream, content_type='video/mp4')
        resp['Content-Disposition'] = 'inline; filename="video.mp4"'
        resp['Accept-Ranges'] = 'bytes'
        return resp
    except Exception as e:
        return HttpResponse(f'Failed to stream video: {e}', status=500)


# ---------------------------------------------------------------------------
# Video ingestion view
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def ingest_video_view(request):
    """
    Ingest a video from Google Drive into the evidence database.

    Request body (JSON):
        gdrive_url  (str)   – Google Drive share URL or file ID
        cam_id      (str)   – Camera identifier (e.g. "CAM-001")
        gps_lat     (float) – Latitude of camera location
        gps_lng     (float) – Longitude of camera location
        skip_existing (bool, optional) – Skip already-ingested frames (default True)

    Response:
        200 { "frames_ingested": <int>, "cam_id": <str> }
        400 { "error": <str> }
        500 { "error": <str> }
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse({"error": f"Invalid JSON body: {exc}"}, status=400)

    gdrive_url = body.get("gdrive_url", "").strip()
    cam_id = body.get("cam_id", "").strip()
    gps_lat = body.get("gps_lat")
    gps_lng = body.get("gps_lng")

    if not gdrive_url:
        return JsonResponse({"error": "gdrive_url is required"}, status=400)
    if not cam_id:
        return JsonResponse({"error": "cam_id is required"}, status=400)
    if gps_lat is None or gps_lng is None:
        return JsonResponse({"error": "gps_lat and gps_lng are required"}, status=400)

    try:
        gps_lat = float(gps_lat)
        gps_lng = float(gps_lng)
    except (TypeError, ValueError):
        return JsonResponse({"error": "gps_lat and gps_lng must be numbers"}, status=400)

    skip_existing = bool(body.get("skip_existing", True))

    try:
        from multimedia_rag.ingestion import ingest_video
        frames_ingested = ingest_video(
            gdrive_url=gdrive_url,
            cam_id=cam_id,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            skip_existing=skip_existing,
        )
        return JsonResponse({"frames_ingested": frames_ingested, "cam_id": cam_id})
    except Exception as exc:
        logger.exception("Ingestion failed for %s", gdrive_url)
        return JsonResponse({"error": str(exc)}, status=500)
