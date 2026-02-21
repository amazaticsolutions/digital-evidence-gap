"""
Keyword-based text search fallback for the RAG pipeline.

When vector search returns few or no results, keyword search provides
a safety net by using MongoDB's $text index across the three caption
fields (brief / detailed / regional).

Functions:
    keyword_search: Run MongoDB $text search on caption fields
    combined_search: Merge vector + keyword results with score boosting
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List

from pymongo.errors import PyMongoError

from multimedia_rag.ingestion.mongo_store import get_db, ensure_text_index
from multimedia_rag.query.search import multi_search
from multimedia_rag import config

logger = logging.getLogger(__name__)

# Stop-words stripped before building the keyword query
_STOP_WORDS = frozenset({
    "a", "an", "the", "in", "on", "at", "of", "to", "for", "is", "are",
    "was", "were", "be", "been", "being", "it", "its", "this", "that",
    "and", "or", "but", "not", "with", "from", "by", "as", "into",
    "about", "between", "through", "during", "before", "after",
    "me", "my", "i", "we", "you", "he", "she", "they", "them",
    "show", "find", "every", "all", "any", "each", "some",
})

# Boost factor applied when a frame appears in BOTH vector and keyword results
_DUAL_MATCH_BOOST = 1.2


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def _extract_keywords(query: str) -> str:
    """
    Strip stop-words and return a space-separated keyword string for $text.

    Args:
        query: Raw user query.

    Returns:
        str: Cleaned keywords joined by spaces.
    """
    words = query.lower().split()
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) > 1]
    return " ".join(keywords) if keywords else query


def keyword_search(
    user_query: str,
    top_k: int = 25,
) -> List[Dict[str, Any]]:
    """
    Run a MongoDB $text search across caption fields.

    Requires a compound text index on caption_brief, caption_detailed,
    and caption_regional.  Call ``ensure_text_index()`` once at startup
    or use ``setup_indexes()`` to create it.

    Args:
        user_query: Natural-language search query.
        top_k: Maximum number of results to return.

    Returns:
        List[Dict]: Results in the same format as ``multi_search()``.
            Each dict includes _id, caption_brief, caption_detailed,
            caption_regional, cam_id, timestamp, gdrive_url, and score
            (derived from $textScore normalised to 0-1).

    Example:
        >>> results = keyword_search("red backpack near bin")
        >>> results[0]["score"]
        0.82
    """
    kw = _extract_keywords(user_query)
    if not kw:
        _log("WARNING: No keywords extracted — keyword search skipped")
        return []

    _log(f"Keyword search for: '{kw}'")

    try:
        # Ensure the text index exists (idempotent)
        ensure_text_index()

        db = get_db()
        col = db[config.COLLECTION_FRAME_EMBEDDINGS]

        cursor = col.find(
            {"$text": {"$search": kw}},
            {
                "_id": 1,
                "caption_brief": 1,
                "caption_detailed": 1,
                "caption_regional": 1,
                "cam_id": 1,
                "timestamp": 1,
                "frame_image": 1,
                "gdrive_url": 1,
                "score": {"$meta": "textScore"},
            },
        ).sort([("score", {"$meta": "textScore"})]).limit(top_k)

        results = list(cursor)

        # Normalise textScore into a rough 0-1 range
        if results:
            max_score = max(r.get("score", 1) for r in results) or 1
            for r in results:
                r["score"] = round(r.get("score", 0) / max_score, 4)
                r["matched_query"] = kw

        _log(f"Keyword search returned {len(results)} results")
        return results

    except PyMongoError as e:
        _log(f"ERROR: Keyword search failed: {e}")
        return []
    except Exception as e:
        _log(f"ERROR: Unexpected keyword search error: {e}")
        return []


def combined_search(
    user_query: str,
    top_k: int = 25,
) -> List[Dict[str, Any]]:
    """
    Run multi-index vector search and keyword search in parallel,
    then merge and deduplicate.

    Frames appearing in **both** result sets receive a score boost of
    1.2x (capped at 1.0 for the normalised score).

    Args:
        user_query: Natural-language search query.
        top_k: Maximum number of merged results to return.

    Returns:
        List[Dict]: Merged, deduplicated results sorted by final score
            descending.  Same dict format as ``multi_search()``.

    Example:
        >>> results = combined_search("person drops red backpack")
        >>> len(results) <= 25
        True
    """
    _log("Starting combined (vector + keyword) search...")

    vector_results: List[Dict[str, Any]] = []
    kw_results: List[Dict[str, Any]] = []

    # Run both searches in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_vec = executor.submit(multi_search, user_query, top_k)
        future_kw = executor.submit(keyword_search, user_query, top_k)

        for future in as_completed([future_vec, future_kw]):
            try:
                if future is future_vec:
                    vector_results = future.result()
                else:
                    kw_results = future.result()
            except Exception as e:
                _log(f"WARNING: One search branch failed: {e}")

    # Collect IDs from each source for boost detection
    vector_ids = {r["_id"] for r in vector_results if "_id" in r}
    keyword_ids = {r["_id"] for r in kw_results if "_id" in r}
    both_ids = vector_ids & keyword_ids

    # Merge into a single dict keyed by _id (keep highest score)
    best: Dict[str, Dict[str, Any]] = {}
    for hit in vector_results + kw_results:
        fid = hit.get("_id")
        if fid is None:
            continue
        score = hit.get("score", 0)

        # Boost if present in both sets
        if fid in both_ids:
            score = min(score * _DUAL_MATCH_BOOST, 1.0)
            hit["score"] = score

        existing = best.get(fid)
        if existing is None or score > existing.get("score", 0):
            best[fid] = hit

    merged = sorted(best.values(), key=lambda x: x.get("score", 0), reverse=True)
    results = merged[:top_k]

    _log(
        f"Combined search: {len(vector_results)} vector + {len(kw_results)} keyword "
        f"→ {len(results)} merged results ({len(both_ids)} boosted)"
    )
    return results
