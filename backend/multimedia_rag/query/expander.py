"""
Query expansion module using Ollama LLM.

This module rewrites a user query into multiple phrasings to increase
recall during vector search. The LLM generates 5 alternative phrasings
that mean the same thing but use different vocabulary, focusing on how
a CCTV caption might describe the same scene.

Functions:
    expand_query: Expand a single user query into 6 phrasings
                  (original + 5 rephrased versions)
"""

import json
import re
import logging
from datetime import datetime
from typing import List

import ollama

from multimedia_rag import config

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# Prompt template for query expansion
_EXPANSION_PROMPT = (
    "You are a forensic analyst assistant.\n"
    "Rewrite the following query in 5 different ways "
    "using different vocabulary but the same meaning.\n"
    "Focus on how a CCTV caption might describe the same scene.\n"
    "Return ONLY a JSON array of 5 strings.\n"
    "No explanation. No markdown. Start with [ end with ]\n"
    "Query: {user_query}"
)


def expand_query(user_query: str) -> List[str]:
    """
    Expand a user query into 6 phrasings (original + 5 rephrased).

    Uses Ollama to rewrite the user query in 5 different ways that
    preserve the semantic meaning but use alternative vocabulary,
    especially vocabulary likely found in CCTV captions.

    If the Ollama call or JSON parsing fails the function falls back
    to returning a list containing only the original query so the
    pipeline never crashes.

    Args:
        user_query: The original natural-language search query.

    Returns:
        List[str]: A list of 6 strings — the original query followed
            by 5 rephrased versions. On failure returns [user_query].

    Example:
        >>> expand_query("suspect fleeing the scene")
        [
            "suspect fleeing the scene",
            "person running away quickly",
            "individual moving fast toward exit",
            "man escaping from location",
            "someone leaving in a hurry",
            "person sprinting away from area",
        ]
    """
    if not user_query or not user_query.strip():
        return [user_query] if user_query else [""]

    _log(f"Expanding query: '{user_query}'")

    prompt = _EXPANSION_PROMPT.format(user_query=user_query)

    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        response = client.generate(
            model=config.LLM_MODEL,
            prompt=prompt,
            options={
                "temperature": 0.7,
                "num_predict": 400,
            },
        )
        raw = response.get("response", "").strip()

        if not raw:
            _log("WARNING: Ollama returned empty response for query expansion")
            return [user_query]

        # --- Three-layer JSON parser ---
        rephrased: List[str] = []

        # Layer 1: direct parse
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                rephrased = [str(s).strip() for s in parsed if s]
        except json.JSONDecodeError:
            pass

        # Layer 2: regex extraction
        if not rephrased:
            match = re.search(r"\[[\s\S]*?\]", raw)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list):
                        rephrased = [str(s).strip() for s in parsed if s]
                except json.JSONDecodeError:
                    pass

        # Layer 3: give up, use original only
        if not rephrased:
            _log(f"WARNING: Could not parse expanded queries from: {raw[:200]}")
            return [user_query]

        # Ensure original query is always first
        if user_query not in rephrased:
            rephrased.insert(0, user_query)
        else:
            # Move to front if present elsewhere
            rephrased.remove(user_query)
            rephrased.insert(0, user_query)

        _log(f"Expanded to {len(rephrased)} query phrasings")
        return rephrased

    except Exception as e:
        _log(f"WARNING: Query expansion failed ({e}). Using original query only.")
        return [user_query]
