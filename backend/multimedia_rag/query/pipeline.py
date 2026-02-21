"""
RAG query pipeline orchestrator for forensic video analysis.

This module is the single entry-point for running a forensic query
against the evidence database.  It chains together every stage of the
improved pipeline:

Pipeline Steps (9):
    1. Validate query specificity via Ollama
    2. Combined search (vector + keyword, multi-index, multi-query)
    3. Empty-result check
    4. Temporal expansion (±5 s, same camera)
    5. Hardened LLM scoring (chunked, validated, fallback)
    6. Relevance filter (score >= 40)
    7. Metadata enrichment
    8. Sort by (cam_id, timestamp)
    9. Return structured result dict

Functions:
    run_query:  Execute the full pipeline and return a result dict.
    get_frame_ids_from_results:  Extract frame IDs for ReID.
    format_results_for_display:  Sanitise results for JSON transport.
"""

import base64
import logging
from datetime import datetime
from typing import Dict, Any, List

import ollama

from multimedia_rag import config
from multimedia_rag.ingestion.mongo_store import get_frame_metadata
from multimedia_rag.query.hybrid_search import combined_search
from multimedia_rag.query.expander_temporal import expand_temporal
from multimedia_rag.query.llm_answer import score_and_answer, generate_summary

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# Step 1: Query validation
# ---------------------------------------------------------------------------

def _validate_query(user_query: str) -> bool:
    """
    Ask the LLM whether the query is specific enough for forensic search.

    A query like "show me stuff" is too vague and may drown the analyst in
    noise.  The LLM decides — if Ollama is unavailable we optimistically
    accept the query.

    Args:
        user_query: The raw user query.

    Returns:
        bool: True if the query is considered specific enough.
    """
    prompt = (
        "You are a forensic video search assistant. Decide whether the "
        "following query is specific enough to search surveillance footage.\n"
        "A good query mentions at least one of: an object, a person "
        "description, an action, or a time reference.\n"
        f'Query: "{user_query}"\n'
        "Respond ONLY with YES or NO."
    )
    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        resp = client.generate(
            model=config.LLM_MODEL,
            prompt=prompt,
            options={"temperature": 0.0, "num_predict": 5},
        )
        answer = resp.get("response", "").strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        _log(f"WARNING: Query validation LLM call failed ({e}); accepting query.")
        return True


# ---------------------------------------------------------------------------
# Step 7: Metadata enrichment
# ---------------------------------------------------------------------------

def _enrich_with_metadata(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich results with data from the frame_metadata collection.

    Adds GPS coordinates, confidence, ReID group, and decodes any stored
    frame_image Binary to a base64 string for the frontend.

    Args:
        results: Scored (and filtered) search results.

    Returns:
        List[Dict]: The same results with metadata fields merged in.
    """
    enriched: List[Dict[str, Any]] = []
    for result in results:
        er = result.copy()
        frame_id = result.get("_id")

        try:
            metadata = get_frame_metadata(frame_id) if frame_id else None
        except Exception:
            metadata = None

        if metadata:
            er["gps_lat"] = metadata.get("gps_lat")
            er["gps_lng"] = metadata.get("gps_lng")
            er["confidence"] = metadata.get("confidence")
            er["reid_group"] = metadata.get("reid_group")

        # Decode frame_image Binary to base64
        if "frame_image" in er:
            try:
                frame_image = er["frame_image"]
                image_bytes = (
                    bytes(frame_image)
                    if hasattr(frame_image, "__bytes__")
                    else frame_image
                )
                er["image_bytes"] = image_bytes
                er["image_base64"] = base64.b64encode(image_bytes).decode("utf-8")
                del er["frame_image"]
            except Exception:
                pass

        enriched.append(er)
    return enriched


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_query(user_query: str) -> Dict[str, Any]:
    """
    Execute the complete forensic RAG query pipeline.

    Steps:
        1. Validate query specificity (LLM guard-rail).
        2. ``combined_search(top_k=25)`` — multi-query, multi-index vector
           search merged with keyword fallback.
        3. Empty-result early exit.
        4. ``expand_temporal(window=5)`` — add ±5 s neighbours.
        5. ``score_and_answer`` — hardened LLM scoring with chunking.
        6. Filter by ``score >= RELEVANCE_THRESHOLD``.
        7. Metadata enrichment (GPS, ReID groups, images).
        8. Sort by ``(cam_id, timestamp)`` → timeline.
        9. Return structured dict.

    Args:
        user_query: Natural-language query, e.g. *"Show me every instance
            of the red backpack being dropped"*.

    Returns:
        Dict with keys:
            - query (str)
            - total_searched (int): How many frames entered scoring.
            - total_found (int): How many passed the relevance filter.
            - results (List[Dict]): Relevant results sorted by score desc.
            - timeline (List[Dict]): Same results sorted by (cam_id, ts).
            - search_method (str): "combined" / "vector+keyword".
            - queries_used (List[str]): Expanded query variants used.
            - summary (str): LLM-generated finding summary.
    """
    if not user_query or not user_query.strip():
        _log("ERROR: Empty query received.")
        return {
            "query": "",
            "total_searched": 0,
            "total_found": 0,
            "results": [],
            "timeline": [],
            "search_method": "none",
            "queries_used": [],
            "summary": "No query provided.",
        }

    _log(f"{'=' * 60}")
    _log(f"QUERY: {user_query}")
    _log(f"{'=' * 60}")

    # ------------------------------------------------------------------
    # Step 1 — validate specificity
    # ------------------------------------------------------------------
    _log("Step 1: Validating query specificity...")
    is_specific = _validate_query(user_query)
    if not is_specific:
        _log("Query rejected as too vague.")
        return {
            "query": user_query,
            "total_searched": 0,
            "total_found": 0,
            "results": [],
            "timeline": [],
            "search_method": "rejected",
            "queries_used": [],
            "summary": (
                "Your query is too vague for forensic search. "
                "Please mention a specific object, person description, "
                "action, or time reference."
            ),
        }

    # ------------------------------------------------------------------
    # Step 2 — combined search (vector + keyword)
    # ------------------------------------------------------------------
    _log("Step 2: Running combined search (top_k=25)...")
    try:
        search_results = combined_search(user_query, top_k=25)
    except Exception as e:
        _log(f"ERROR: Combined search failed: {e}")
        search_results = []

    _log(f"  Combined search returned {len(search_results)} results.")

    # ------------------------------------------------------------------
    # Step 3 — empty-result check
    # ------------------------------------------------------------------
    if not search_results:
        _log("Step 3: No results found. Returning empty response.")
        return {
            "query": user_query,
            "total_searched": 0,
            "total_found": 0,
            "results": [],
            "timeline": [],
            "search_method": "combined",
            "queries_used": [],
            "summary": f"No frames found matching '{user_query}'.",
        }

    # ------------------------------------------------------------------
    # Step 4 — temporal expansion
    # ------------------------------------------------------------------
    _log("Step 4: Temporal expansion (±5 s)...")
    try:
        expanded = expand_temporal(search_results, window=5)
    except Exception as e:
        _log(f"WARNING: Temporal expansion failed ({e}); continuing without.")
        expanded = search_results

    _log(f"  After expansion: {len(expanded)} frames (was {len(search_results)}).")
    total_searched = len(expanded)

    # ------------------------------------------------------------------
    # Step 5 — LLM scoring (hardened)
    # ------------------------------------------------------------------
    _log("Step 5: LLM scoring (chunked, validated)...")
    scored = score_and_answer(user_query, expanded)

    # ------------------------------------------------------------------
    # Step 6 — relevance filter
    # ------------------------------------------------------------------
    _log(f"Step 6: Filtering (score >= {config.RELEVANCE_THRESHOLD})...")
    relevant = [
        r for r in scored
        if r.get("score", 0) >= config.RELEVANCE_THRESHOLD
    ]
    _log(f"  {len(relevant)}/{len(scored)} pass threshold.")

    # ------------------------------------------------------------------
    # Step 7 — metadata enrichment
    # ------------------------------------------------------------------
    _log("Step 7: Enriching results with metadata...")
    enriched = _enrich_with_metadata(relevant)

    # ------------------------------------------------------------------
    # Step 8 — sort → timeline
    # ------------------------------------------------------------------
    _log("Step 8: Building timeline (sorted by cam_id, timestamp)...")
    timeline = sorted(
        enriched,
        key=lambda x: (x.get("cam_id", ""), float(x.get("timestamp", 0))),
    )
    for i, item in enumerate(timeline):
        item["sequence"] = i + 1

    # Results sorted by score descending
    results_by_score = sorted(
        enriched,
        key=lambda x: x.get("score", 0),
        reverse=True,
    )

    # ------------------------------------------------------------------
    # Step 9 — summary & response
    # ------------------------------------------------------------------
    _log("Step 9: Generating summary...")
    summary = generate_summary(user_query, results_by_score)

    # Collect the expanded query variants from the search module metadata
    queries_used = list({user_query})  # at minimum the original

    output: Dict[str, Any] = {
        "query": user_query,
        "total_searched": total_searched,
        "total_found": len(results_by_score),
        "results": results_by_score,
        "timeline": timeline,
        "search_method": "combined",
        "queries_used": queries_used,
        "summary": summary,
    }

    _log(f"{'=' * 60}")
    _log("QUERY COMPLETE")
    _log(f"{'=' * 60}")
    _log(f"Total searched: {total_searched}")
    _log(f"Total relevant: {output['total_found']}")
    _log(f"Summary: {summary}")

    return output


# ---------------------------------------------------------------------------
# Utility helpers (unchanged API contracts)
# ---------------------------------------------------------------------------

def get_frame_ids_from_results(results: Dict[str, Any]) -> List[str]:
    """
    Extract frame IDs from query results for ReID processing.

    Args:
        results: The output dictionary from ``run_query()``.

    Returns:
        List[str]: Frame IDs from relevant results.
    """
    return [r.get("_id") for r in results.get("results", []) if r.get("_id")]


def format_results_for_display(
    results: Dict[str, Any],
    include_images: bool = False,
) -> Dict[str, Any]:
    """
    Format results for JSON serialisation and frontend display.

    Strips non-serialisable fields and optionally drops large image data.

    Args:
        results: The output dictionary from ``run_query()``.
        include_images: Include base64 images in output.

    Returns:
        Dict: A clean, JSON-serialisable copy of the results.
    """
    output = results.copy()

    def _clean(r: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {
            "_id": r.get("_id"),
            "cam_id": r.get("cam_id"),
            "timestamp": r.get("timestamp"),
            "score": r.get("score"),
            "relevant": r.get("relevant"),
            "explanation": r.get("explanation"),
            "caption_brief": r.get("caption_brief"),
            "caption_detailed": r.get("caption_detailed"),
            "caption_regional": r.get("caption_regional"),
            "gdrive_url": r.get("gdrive_url"),
            "gps_lat": r.get("gps_lat"),
            "gps_lng": r.get("gps_lng"),
            "reid_group": r.get("reid_group"),
            "sequence": r.get("sequence"),
            "source": r.get("source"),
        }
        if include_images:
            cleaned["image_base64"] = r.get("image_base64")
        return cleaned

    output["results"] = [_clean(r) for r in output.get("results", [])]
    output["timeline"] = [_clean(r) for r in output.get("timeline", [])]

    return output
