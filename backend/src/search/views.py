"""
Search views — forensic query endpoint.

Endpoints:
    POST /api/search/query/
         Body: {"query": str, "include_images": bool (optional, default false)}

    POST /api/search/reid/
         Body: {"frame_ids": [str, ...]}
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Query endpoint
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def query_view(request):
    """
    Run a forensic RAG query against the evidence database.

    Request body (JSON):
        query          (str)            – Natural language query
        include_images (bool, optional) – Include base64 frame images (default False)

    Response (200):
        {
            "query": str,
            "total_searched": int,
            "total_found": int,
            "results": [...],
            "timeline": [...],
            "search_method": str,
            "queries_used": [...],
            "summary": str
        }
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse({"error": f"Invalid JSON body: {exc}"}, status=400)

    user_query = (body.get("query") or "").strip()
    if not user_query:
        return JsonResponse({"error": "query is required"}, status=400)

    include_images = bool(body.get("include_images", False))

    try:
        from multimedia_rag.query.pipeline import run_query, format_results_for_display
        raw = run_query(user_query)
        formatted = format_results_for_display(raw, include_images=include_images)
        return JsonResponse(formatted)
    except Exception as exc:
        logger.exception("Query pipeline failed for: %s", user_query)
        return JsonResponse({"error": str(exc)}, status=500)


# ---------------------------------------------------------------------------
# Re-ID endpoint
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def reid_view(request):
    """
    Run person re-identification on a set of frame IDs.

    Request body (JSON):
        frame_ids (list[str]) – Frame document IDs from a previous query

    Response (200):
        { "reid_results": {...} }
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError) as exc:
        return JsonResponse({"error": f"Invalid JSON body: {exc}"}, status=400)

    frame_ids = body.get("frame_ids")
    if not isinstance(frame_ids, list) or not frame_ids:
        return JsonResponse({"error": "frame_ids must be a non-empty list"}, status=400)

    try:
        from multimedia_rag.query.reid import run_reid
        reid_results = run_reid(frame_ids)
        return JsonResponse({"reid_results": reid_results})
    except Exception as exc:
        logger.exception("ReID failed for frame_ids: %s", frame_ids)
        return JsonResponse({"error": str(exc)}, status=500)
