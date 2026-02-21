"""
Temporal expansion module for the forensic RAG pipeline.

After scoring, relevant frames may have neighbours that provide context
(e.g. a suspect walking up to a car seconds before the key frame).  This
module fetches frames ±N seconds from the same camera and injects them
into the result list so the analyst sees the full clip, not just one
isolated frame.

Functions:
    expand_temporal:  Expand results by adding neighbouring frames.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from multimedia_rag import config
from multimedia_rag.ingestion.mongo_store import get_db

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def expand_temporal(
    results: List[Dict[str, Any]],
    window: int = 5,
) -> List[Dict[str, Any]]:
    """
    Expand scored results by including neighbouring frames.

    For every result at timestamp **T** from camera **C**, query MongoDB
    for all frames where ``cam_id == C`` and ``T - window <= timestamp <= T + window``.
    Newly discovered frames are appended with ``source = "temporal_expansion"``
    and their score is set to ``parent_score × 0.7``.  Duplicates (by ``_id``)
    are removed, keeping the copy with the higher score.

    Args:
        results: Scored search results. Each dict must contain at least:
            ``_id``, ``cam_id``, ``timestamp``, ``score``.
        window: Number of seconds to expand in each direction (default 5).

    Returns:
        List[Dict]: The original results plus any newly discovered
        temporal neighbours, sorted by (cam_id, timestamp).
    """
    if not results:
        return results

    _log(f"Temporal expansion: ±{window}s for {len(results)} results")

    try:
        db = get_db()
        collection = db[config.COLLECTION_FRAME_EMBEDDINGS]
    except Exception as e:
        _log(f"WARNING: MongoDB connection failed in temporal expansion: {e}")
        return results

    # Collect existing _ids so we know what's new
    seen_ids: Dict[str, Dict[str, Any]] = {}
    for r in results:
        fid = r.get("_id")
        if fid:
            seen_ids[fid] = r

    new_frames: List[Dict[str, Any]] = []

    for result in results:
        cam_id = result.get("cam_id")
        timestamp = result.get("timestamp")
        parent_score = float(result.get("score", 0))

        if cam_id is None or timestamp is None:
            continue

        try:
            timestamp = float(timestamp)
        except (TypeError, ValueError):
            continue

        try:
            neighbours = list(
                collection.find(
                    {
                        "cam_id": cam_id,
                        "timestamp": {
                            "$gte": timestamp - window,
                            "$lte": timestamp + window,
                        },
                    },
                    {
                        "_id": 1,
                        "cam_id": 1,
                        "timestamp": 1,
                        "caption_brief": 1,
                        "caption_detailed": 1,
                        "caption_regional": 1,
                        "video_id": 1,
                        "frame_path": 1,
                    },
                )
            )
        except Exception as e:
            _log(f"WARNING: Temporal query failed for cam={cam_id} t={timestamp}: {e}")
            continue

        for nb in neighbours:
            nid = str(nb.get("_id"))
            if nid in seen_ids:
                continue  # already present

            nb_frame: Dict[str, Any] = {
                "_id": nid,
                "cam_id": nb.get("cam_id"),
                "timestamp": nb.get("timestamp"),
                "caption_brief": nb.get("caption_brief", ""),
                "caption_detailed": nb.get("caption_detailed", ""),
                "caption_regional": nb.get("caption_regional", ""),
                "video_id": nb.get("video_id"),
                "frame_path": nb.get("frame_path"),
                "score": round(parent_score * 0.7, 1),
                "relevant": (parent_score * 0.7) >= config.RELEVANCE_THRESHOLD,
                "explanation": "Temporal neighbour of a relevant frame",
                "source": "temporal_expansion",
            }
            seen_ids[nid] = nb_frame
            new_frames.append(nb_frame)

    _log(f"Temporal expansion added {len(new_frames)} neighbour frames")

    # Combine and sort by (cam_id, timestamp)
    combined = list(seen_ids.values())
    combined.sort(key=lambda x: (x.get("cam_id", ""), float(x.get("timestamp", 0))))

    return combined
