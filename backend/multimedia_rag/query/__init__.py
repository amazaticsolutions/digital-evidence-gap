"""
Query package for the Multimedia RAG Engine.

This package provides the complete query pipeline for searching and
analyzing forensic video evidence, including:
- Vector similarity search in MongoDB Atlas
- LLM-based relevance scoring and explanation
- Complete RAG pipeline orchestration
- Person re-identification across cameras

Main functions:
    run_query: Execute the complete RAG query pipeline
    run_reid: Run person re-identification on results

Sub-modules:
    search: MongoDB Atlas vector search
    llm_answer: LLM scoring and answering
    pipeline: LangChain RAG pipeline
    reid: Person re-identification with torchreid
"""

from multimedia_rag.query.pipeline import run_query, get_frame_ids_from_results, format_results_for_display
from multimedia_rag.query.search import vector_search
from multimedia_rag.query.llm_answer import score_and_answer
from multimedia_rag.query.reid import run_reid


__all__ = [
    'run_query',
    'run_reid',
    'vector_search',
    'score_and_answer',
    'get_frame_ids_from_results',
    'format_results_for_display'
]
