"""
Query package for the Multimedia RAG Engine.

This package provides the complete query pipeline for searching and
analyzing forensic video evidence, including:
- Multi-query, multi-index vector search with keyword fallback
- Query expansion via LLM
- Temporal frame expansion (±N seconds)
- Hardened LLM scoring with chunking and validation
- Complete RAG pipeline orchestration
- Person re-identification across cameras

Main functions:
    run_query: Execute the complete RAG query pipeline
    run_reid: Run person re-identification on results

Sub-modules:
    search:             Multi-index vector search
    hybrid_search:      Keyword + combined search
    expander:           LLM-based query expansion
    expander_temporal:  Time-window frame expansion
    llm_answer:         Hardened LLM scoring
    pipeline:           Pipeline orchestrator
    reid:               Person re-identification with torchreid
"""

from multimedia_rag.query.pipeline import run_query, get_frame_ids_from_results, format_results_for_display
from multimedia_rag.query.search import vector_search, multi_search
from multimedia_rag.query.hybrid_search import combined_search, keyword_search
from multimedia_rag.query.expander import expand_query
from multimedia_rag.query.expander_temporal import expand_temporal
from multimedia_rag.query.llm_answer import score_and_answer

# Lazy import for reid — torchreid is an optional heavy dependency
try:
    from multimedia_rag.query.reid import run_reid
except ImportError:
    def run_reid(*args, **kwargs):  # type: ignore
        raise ImportError(
            "torchreid is required for ReID. "
            "Install it with: pip install torchreid"
        )


__all__ = [
    "run_query",
    "run_reid",
    "vector_search",
    "multi_search",
    "combined_search",
    "keyword_search",
    "expand_query",
    "expand_temporal",
    "score_and_answer",
    "get_frame_ids_from_results",
    "format_results_for_display",
]
