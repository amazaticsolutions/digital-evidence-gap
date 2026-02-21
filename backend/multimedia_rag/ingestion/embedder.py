"""
Text embedding module using Sentence Transformers.

This module provides functionality to generate dense vector embeddings
from text using the all-MiniLM-L6-v2 model from Sentence Transformers.
The model produces 384-dimensional vectors suitable for semantic similarity
search and RAG applications.

IMPORTANT: The model is loaded once at module import time and reused for
all subsequent calls. This ensures consistent embeddings between ingestion
and query phases and improves performance.

Functions:
    generate_embedding: Generate a 384-dim embedding for a single text string
    generate_embeddings_for_captions: Generate three embeddings from a caption dict
    generate_embeddings_batch: Generate embeddings for multiple texts efficiently
"""

import logging
from datetime import datetime
from typing import Dict, List, Union

from sentence_transformers import SentenceTransformer

from multimedia_rag import config

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# =============================================================================
# Module-level model loading (loaded once, reused for all calls)
# =============================================================================

_log(f"Loading embedding model: {config.EMBEDDING_MODEL}...")
_embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
_log(f"Embedding model loaded. Vector dimension: {config.EMBEDDING_DIMENSION}")


def generate_embedding(text: str) -> List[float]:
    """
    Generate a dense vector embedding for a single input text.

    Uses the all-MiniLM-L6-v2 model to encode text into a 384-dimensional
    vector. The same model instance is used for both ingestion (encoding
    captions) and query (encoding user questions) to ensure semantic
    consistency.

    Args:
        text: The input text to embed. Can be a caption or a query.

    Returns:
        List[float]: A list of 384 floating point numbers representing
            the semantic embedding of the input text.

    Raises:
        ValueError: If the input text is empty or None.
        RuntimeError: If the model fails to generate an embedding.

    Example:
        >>> embedding = generate_embedding("A person in a red jacket walking")
        >>> len(embedding)
        384
    """
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty")

    try:
        embedding = _embedding_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        embedding_list = embedding.tolist()

        if len(embedding_list) != config.EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"Unexpected embedding dimension: {len(embedding_list)} "
                f"(expected {config.EMBEDDING_DIMENSION})"
            )
        return embedding_list

    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {e}")


def generate_embeddings_for_captions(captions: Dict[str, str]) -> Dict[str, List[float]]:
    """
    Generate one embedding for each of the three caption levels.

    Accepts the caption dict produced by the Florence-2 captioner and
    returns a dict with three corresponding embeddings.

    Args:
        captions: Dictionary with keys 'brief', 'detailed', 'regional',
            each mapping to a caption string.

    Returns:
        Dict[str, List[float]]: Dictionary with keys:
            - 'embedding_brief':    384-float embedding of the brief caption.
            - 'embedding_detailed': 384-float embedding of the detailed caption.
            - 'embedding_regional': 384-float embedding of the regional caption.

    Raises:
        ValueError: If any required caption key is missing or empty.
        RuntimeError: If the model fails to generate an embedding.

    Example:
        >>> caps = {
        ...     "brief": "Man near trash can",
        ...     "detailed": "Man in red jacket standing next to blue bin",
        ...     "regional": "Center: man bending. Right: blue bin."
        ... }
        >>> embs = generate_embeddings_for_captions(caps)
        >>> len(embs["embedding_brief"])
        384
    """
    required_keys = ("brief", "detailed", "regional")
    for key in required_keys:
        if key not in captions or not captions[key] or not str(captions[key]).strip():
            raise ValueError(f"Caption key '{key}' is missing or empty")

    texts = [
        str(captions["brief"]).strip(),
        str(captions["detailed"]).strip(),
        str(captions["regional"]).strip(),
    ]

    try:
        embeddings = _embedding_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        result = {
            "embedding_brief": embeddings[0].tolist(),
            "embedding_detailed": embeddings[1].tolist(),
            "embedding_regional": embeddings[2].tolist(),
        }

        # Verify dimensions
        for name, vec in result.items():
            if len(vec) != config.EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"{name} dimension {len(vec)} != expected {config.EMBEDDING_DIMENSION}"
                )

        return result

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Multi-embedding generation failed: {e}")


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently in a batch.

    Processes multiple texts in a single call, which is more efficient
    than calling generate_embedding() repeatedly.

    Args:
        texts: List of text strings to embed.

    Returns:
        List[List[float]]: A list of embeddings, one per input text.
            Each embedding is a list of 384 floats.

    Raises:
        ValueError: If the input list is empty or contains empty strings.
        RuntimeError: If the model fails to generate embeddings.
    """
    if not texts:
        raise ValueError("Input text list cannot be empty")

    valid_texts = []
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(f"Text at index {i} is empty")
        valid_texts.append(text.strip())

    try:
        embeddings = _embedding_model.encode(
            valid_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(valid_texts) > 10,
        )
        return [emb.tolist() for emb in embeddings]

    except Exception as e:
        raise RuntimeError(f"Batch embedding generation failed: {e}")


def get_model_info() -> dict:
    """
    Get information about the loaded embedding model.

    Returns:
        dict: Dictionary containing model_name, dimension, and max_seq_length.
    """
    return {
        "model_name": config.EMBEDDING_MODEL,
        "dimension": config.EMBEDDING_DIMENSION,
        "max_seq_length": _embedding_model.max_seq_length,
    }
