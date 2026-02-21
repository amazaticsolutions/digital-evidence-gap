"""
Hardened LLM answer and scoring module using Ollama.

This module uses a local LLM (llama3 / mistral) via Ollama to score
search results for relevance and provide explanations.  It is designed
to NEVER crash, even when Ollama returns malformed JSON.

Key hardening features:
    - Three-layer JSON parser (direct → regex → fallback)
    - Per-field validation of every score item
    - Automatic chunking for large result sets (>15 items)
    - Full fallback to vector similarity scores when LLM fails

Functions:
    score_and_answer:  Score search results with hardened parser
    generate_summary:  Generate a natural-language finding summary
    check_llm_available: Verify Ollama availability
"""

import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any

import ollama

from multimedia_rag import config

logger = logging.getLogger(__name__)

# Maximum results per Ollama call before chunking
_CHUNK_SIZE = 10


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

SCORING_PROMPT_TEMPLATE = """You are a forensic video analyst assistant. Your task is to evaluate how relevant each frame description is to the user's query.

USER QUERY: {query}

Below are descriptions of video frames from surveillance footage. For each frame, analyze how well it matches the query and provide:
1. A relevance score from 0 to 100 (100 = perfect match, 0 = completely irrelevant)
2. Whether it's relevant (true if score > 40, false otherwise)
3. A brief explanation of why it is or isn't relevant

FRAME DESCRIPTIONS:
{frame_descriptions}

Respond ONLY with a JSON array.
No explanation. No preamble. No markdown fences.
Your response must start with [ and end with ]
Each item must have these exact keys:
frame_id, score, relevant, explanation"""


# ---------------------------------------------------------------------------
# Three-layer JSON parser
# ---------------------------------------------------------------------------

def _parse_llm_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse an LLM response into a list of score dicts.

    Uses three layers of increasingly aggressive extraction:
        Layer 1 — ``json.loads()`` on the raw text.
        Layer 2 — regex to find ``[...]`` block, then ``json.loads()``.
        Layer 3 — return empty list and log the failure.

    Args:
        response_text: Raw text response from the LLM.

    Returns:
        List[Dict]: Parsed items, or empty list on failure.
    """
    text = response_text.strip()

    # Layer 1: direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    # Layer 2: regex extraction
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Layer 3: give up
    _log(f"WARNING: Could not parse LLM JSON. Raw preview: {text[:300]}")
    return []


# ---------------------------------------------------------------------------
# Per-item validation
# ---------------------------------------------------------------------------

def _validate_score_item(
    item: Any,
    valid_frame_ids: set,
) -> Dict[str, Any] | None:
    """
    Validate a single score item returned by the LLM.

    Rules checked:
        - frame_id is a string present in *valid_frame_ids*
        - score is a number in [0, 100]
        - relevant is a boolean
        - explanation is a non-empty string

    Args:
        item: A single dict from the parsed JSON array.
        valid_frame_ids: Set of _id strings from the actual results.

    Returns:
        The validated dict, or None if the item is invalid.
    """
    if not isinstance(item, dict):
        return None

    frame_id = item.get("frame_id")
    if not isinstance(frame_id, str) or frame_id not in valid_frame_ids:
        return None

    score = item.get("score")
    if isinstance(score, (int, float)):
        score = float(score)
        if score < 0 or score > 100:
            return None
    else:
        return None

    relevant = item.get("relevant")
    if not isinstance(relevant, bool):
        # Accept truthy/falsy ints and strings
        if isinstance(relevant, int):
            relevant = bool(relevant)
        elif isinstance(relevant, str):
            relevant = relevant.lower() in ("true", "1", "yes")
        else:
            return None

    explanation = item.get("explanation", "")
    if not isinstance(explanation, str) or not explanation.strip():
        explanation = "No explanation provided"

    return {
        "frame_id": frame_id,
        "score": score,
        "relevant": relevant,
        "explanation": explanation.strip(),
    }


# ---------------------------------------------------------------------------
# Fallback scoring
# ---------------------------------------------------------------------------

def _fallback_scores(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Produce fallback scores when Ollama is unavailable or returns garbage.

    Uses the MongoDB vector similarity score (0-1) × 100 as relevance.

    Args:
        results: Search results that still carry a vector ``score`` field.

    Returns:
        List[Dict]: The results enriched with score / relevant / explanation.
    """
    _log("Using fallback vector-similarity scoring")
    enriched = []
    for r in results:
        er = r.copy()
        vec_score = float(r.get("score", 0))
        er["score"] = round(vec_score * 100, 1)
        er["relevant"] = er["score"] >= config.RELEVANCE_THRESHOLD
        er["explanation"] = "Scored by vector similarity only (LLM unavailable)"
        enriched.append(er)
    enriched.sort(key=lambda x: x.get("score", 0), reverse=True)
    return enriched


# ---------------------------------------------------------------------------
# Core scoring function — chunk-aware & hardened
# ---------------------------------------------------------------------------

def _score_chunk(
    query: str,
    chunk: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Score a single chunk of results via Ollama.

    Args:
        query: The user query.
        chunk: A subset of search results (max _CHUNK_SIZE items).

    Returns:
        List[Dict]: Validated score items (may be fewer than chunk length).
    """
    frame_descriptions = []
    for i, result in enumerate(chunk):
        fid = result.get("_id", f"frame_{i}")
        # Build a combined caption from the three levels
        caption_parts = []
        for key in ("caption_brief", "caption_detailed", "caption_regional"):
            val = result.get(key)
            if val:
                caption_parts.append(str(val))
        # Fallback to legacy single 'caption' field
        if not caption_parts:
            caption_parts.append(result.get("caption", "No description available"))
        caption_text = " | ".join(caption_parts)

        cam_id = result.get("cam_id", "unknown")
        timestamp = result.get("timestamp", 0)

        frame_descriptions.append(
            f"Frame {i+1}:\n"
            f"  ID: {fid}\n"
            f"  Camera: {cam_id}\n"
            f"  Timestamp: {timestamp}s\n"
            f"  Description: {caption_text}"
        )

    prompt = SCORING_PROMPT_TEMPLATE.format(
        query=query,
        frame_descriptions="\n\n".join(frame_descriptions),
    )

    client = ollama.Client(host=config.OLLAMA_BASE_URL)
    response = client.generate(
        model=config.LLM_MODEL,
        prompt=prompt,
        options={
            "temperature": 0.1,
            "num_predict": 2000,
        },
    )
    raw = response.get("response", "")
    if not raw:
        return []

    parsed = _parse_llm_response(raw)
    valid_ids = {r.get("_id") for r in chunk if r.get("_id")}

    validated = []
    for item in parsed:
        v = _validate_score_item(item, valid_ids)
        if v is not None:
            validated.append(v)

    return validated


def score_and_answer(
    query: str,
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Score search results for relevance using the LLM with full hardening.

    Features:
        - Chunks results into groups of 10 to avoid context overflow.
        - Three-layer JSON parser catches malformed LLM output.
        - Per-field validation rejects invalid score items.
        - Full fallback to vector similarity when Ollama fails.

    Args:
        query: The user's natural-language search query.
        results: Search results from vector / keyword search, each with
            at least _id, cam_id, timestamp, and caption fields.

    Returns:
        List[Dict]: The input results enriched with:
            - score (float 0-100): Relevance score
            - relevant (bool): True if score >= 40
            - explanation (str): Reason for the score
            Sorted by score descending.
    """
    if not query or not query.strip():
        _log("WARNING: Empty query passed to score_and_answer")
        return _fallback_scores(results)

    if not results:
        return []

    _log(f"Scoring {len(results)} results with LLM (chunk size {_CHUNK_SIZE})...")

    try:
        # Split into chunks
        chunks = [
            results[i : i + _CHUNK_SIZE]
            for i in range(0, len(results), _CHUNK_SIZE)
        ]

        all_scores: Dict[str, Dict[str, Any]] = {}
        for ci, chunk in enumerate(chunks):
            _log(f"  Scoring chunk {ci+1}/{len(chunks)} ({len(chunk)} items)...")
            try:
                validated = _score_chunk(query, chunk)
                for v in validated:
                    all_scores[v["frame_id"]] = v
            except Exception as e:
                _log(f"  WARNING: Chunk {ci+1} scoring failed: {e}")
                # Individual chunk failure — continue with next chunk

        # Merge scores into results
        enriched = []
        for result in results:
            er = result.copy()
            fid = result.get("_id")
            if fid and fid in all_scores:
                sd = all_scores[fid]
                er["score"] = sd["score"]
                er["relevant"] = sd["relevant"]
                er["explanation"] = sd["explanation"]
            else:
                # Frame wasn't scored — use vector fallback
                vec_score = float(result.get("score", 0))
                er["score"] = round(vec_score * 100, 1)
                er["relevant"] = er["score"] >= config.RELEVANCE_THRESHOLD
                er["explanation"] = "Scored by vector similarity (LLM did not return score)"

            enriched.append(er)

        enriched.sort(key=lambda x: x.get("score", 0), reverse=True)

        relevant_count = sum(1 for r in enriched if r.get("relevant"))
        _log(f"Scoring complete. {relevant_count} relevant results found.")

        return enriched

    except Exception as e:
        _log(f"ERROR: LLM scoring failed entirely: {e}")
        _log("Falling back to vector similarity scores.")
        return _fallback_scores(results)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def check_llm_available() -> bool:
    """
    Check if the configured LLM model is available on Ollama.

    Handles both the dict response from ollama<=0.1.x and the
    ListResponse Pydantic object from ollama>=0.2.x.

    Returns:
        bool: True if the model is reachable, False otherwise.
    """
    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        response = client.list()

        # ollama<=0.1.x returns a plain dict {"models": [...]}
        # ollama>=0.2.x returns a ListResponse with a .models attribute
        if isinstance(response, dict):
            model_list = response.get("models", [])
        elif hasattr(response, "models"):
            model_list = response.models
        else:
            model_list = []

        names: list = []
        for m in model_list:
            if isinstance(m, dict):
                names.append(m.get("name", "").split(":")[0])
            elif hasattr(m, "model"):
                names.append(str(m.model).split(":")[0])
            elif hasattr(m, "name"):
                names.append(str(m.name).split(":")[0])

        return config.LLM_MODEL in names
    except Exception:
        return False


def generate_summary(
    query: str,
    relevant_results: List[Dict[str, Any]],
) -> str:
    """
    Generate a natural-language summary of the findings.

    Args:
        query: The user's original query.
        relevant_results: Relevant results with scores and explanations.

    Returns:
        str: A 2-3 sentence summary of what was found. Falls back to
            a template string if Ollama is unavailable.
    """
    if not relevant_results:
        return f"No relevant frames found for query: '{query}'"

    summary_prompt = (
        f'Based on these surveillance video analysis results for the query "{query}", '
        "provide a brief 2-3 sentence summary of what was found:\n\n"
        "Results:\n"
        + json.dumps(
            [
                {
                    "frame_id": r.get("_id"),
                    "cam_id": r.get("cam_id"),
                    "timestamp": r.get("timestamp"),
                    "score": r.get("score"),
                    "explanation": r.get("explanation"),
                }
                for r in relevant_results[:5]
            ],
            indent=2,
        )
        + "\n\nSummary:"
    )

    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        response = client.generate(
            model=config.LLM_MODEL,
            prompt=summary_prompt,
            options={"temperature": 0.3, "num_predict": 200},
        )
        text = response.get("response", "").strip()
        if text:
            return text
    except Exception as e:
        _log(f"WARNING: Summary generation failed: {e}")

    # Fallback
    top = relevant_results[0]
    return (
        f"Found {len(relevant_results)} relevant frames for '{query}'. "
        f"Top match: {top.get('_id')} with score {top.get('score')}/100."
    )
