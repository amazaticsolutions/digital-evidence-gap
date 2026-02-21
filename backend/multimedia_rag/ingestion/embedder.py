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
    generate_embedding: Generate a 384-dimensional embedding for input text
    generate_embeddings_batch: Generate embeddings for multiple texts efficiently
"""

from typing import List, Union

from sentence_transformers import SentenceTransformer

from multimedia_rag import config


# =============================================================================
# Module-level model loading (loaded once, reused for all calls)
# =============================================================================

print(f"Loading embedding model: {config.EMBEDDING_MODEL}...")
_embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
print(f"Embedding model loaded. Vector dimension: {config.EMBEDDING_DIMENSION}")


def generate_embedding(text: str) -> List[float]:
    """
    Generate a dense vector embedding for the input text.
    
    This function uses the all-MiniLM-L6-v2 model to encode text into a
    384-dimensional vector. The same model instance is used for both
    ingestion (encoding captions) and query (encoding user questions)
    to ensure semantic consistency.
    
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
        >>> type(embedding[0])
        <class 'float'>
    """
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty")
    
    try:
        # Encode text to embedding vector
        embedding = _embedding_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalize for cosine similarity
        )
        
        # Convert numpy array to Python list of floats
        embedding_list = embedding.tolist()
        
        # Verify dimension
        if len(embedding_list) != config.EMBEDDING_DIMENSION:
            raise RuntimeError(
                f"Unexpected embedding dimension: {len(embedding_list)} "
                f"(expected {config.EMBEDDING_DIMENSION})"
            )
        
        return embedding_list
        
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently in a batch.
    
    This function processes multiple texts in a single call, which is
    more efficient than calling generate_embedding() repeatedly for
    large numbers of texts.
    
    Args:
        texts: List of text strings to embed.
    
    Returns:
        List[List[float]]: A list of embeddings, one per input text.
            Each embedding is a list of 384 floats.
    
    Raises:
        ValueError: If the input list is empty or contains empty strings.
        RuntimeError: If the model fails to generate embeddings.
    
    Example:
        >>> texts = ["A person walking", "A car driving by"]
        >>> embeddings = generate_embeddings_batch(texts)
        >>> len(embeddings)
        2
        >>> len(embeddings[0])
        384
    """
    if not texts:
        raise ValueError("Input text list cannot be empty")
    
    # Filter and validate texts
    valid_texts = []
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(f"Text at index {i} is empty")
        valid_texts.append(text.strip())
    
    try:
        # Batch encode all texts
        embeddings = _embedding_model.encode(
            valid_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(valid_texts) > 10  # Show progress for large batches
        )
        
        # Convert numpy arrays to Python lists
        embeddings_list = [emb.tolist() for emb in embeddings]
        
        return embeddings_list
        
    except Exception as e:
        raise RuntimeError(f"Batch embedding generation failed: {str(e)}")


def get_model_info() -> dict:
    """
    Get information about the loaded embedding model.
    
    Returns:
        dict: Dictionary containing model information:
            - model_name: Name of the model
            - dimension: Output embedding dimension
            - max_seq_length: Maximum input sequence length
    """
    return {
        'model_name': config.EMBEDDING_MODEL,
        'dimension': config.EMBEDDING_DIMENSION,
        'max_seq_length': _embedding_model.max_seq_length
    }
