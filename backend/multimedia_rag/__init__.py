"""
Multimedia RAG Engine for Forensic Video Evidence Analysis.

This package provides a complete pipeline for processing and querying
CCTV video evidence using RAG (Retrieval Augmented Generation) techniques.

Main components:
    - ingestion: Video processing and frame storage pipeline
    - query: RAG query pipeline with vector search and LLM
    - drive: Google Drive integration for video storage

Usage from backend:
    from multimedia_rag.ingestion import ingest_video
    from multimedia_rag.query import run_query, run_reid
"""

__all__ = ['ingest_video', 'run_query', 'run_reid']
__version__ = '1.0.0'

# Lazy imports to avoid circular dependencies
def ingest_video(*args, **kwargs):
    from multimedia_rag.ingestion import ingest_video as _ingest_video
    return _ingest_video(*args, **kwargs)

def run_query(*args, **kwargs):
    from multimedia_rag.query import run_query as _run_query
    return _run_query(*args, **kwargs)

def run_reid(*args, **kwargs):
    from multimedia_rag.query import run_reid as _run_reid
    return _run_reid(*args, **kwargs)
