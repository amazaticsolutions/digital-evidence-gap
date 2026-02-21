"""
RAG query pipeline module using LangChain.

This module orchestrates the complete query pipeline for forensic video
evidence analysis. It combines vector search, LLM scoring, metadata
enrichment, and timeline construction using LangChain for pipeline
orchestration.

Pipeline Steps:
    1. Embed user query using Sentence Transformers
    2. Vector search in MongoDB Atlas
    3. LLM scoring and relevance explanation
    4. Metadata enrichment for relevant results
    5. Timeline construction sorted by timestamp

Functions:
    run_query: Execute the complete RAG query pipeline
"""

import base64
from typing import Dict, Any, List, Optional

from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.schema import Document
from langchain_community.llms import Ollama

from multimedia_rag.ingestion.embedder import generate_embedding
from multimedia_rag.ingestion.mongo_store import get_frame_metadata, get_frame_embedding_doc
from multimedia_rag.query.search import vector_search
from multimedia_rag.query.llm_answer import score_and_answer, generate_summary
from multimedia_rag import config


def _embed_query(query: str) -> Dict[str, Any]:
    """
    Embed the user query and pass it forward with the original query.
    
    Args:
        query: User's natural language query.
    
    Returns:
        Dict containing the original query and its embedding.
    """
    print(f"\nStep 1: Embedding query...")
    embedding = generate_embedding(query)
    return {
        "query": query,
        "embedding": embedding
    }


def _vector_search_step(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform vector search using the query embedding.
    
    Args:
        data: Dict containing query and embedding.
    
    Returns:
        Dict with query, embedding, and search results.
    """
    print(f"Step 2: Performing vector search (top {config.TOP_K_RESULTS})...")
    results = vector_search(
        query_embedding=data["embedding"],
        top_k=config.TOP_K_RESULTS
    )
    return {
        **data,
        "results": results
    }


def _score_results_step(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score results using LLM and add relevance explanations.
    
    Args:
        data: Dict containing query and search results.
    
    Returns:
        Dict with scored and enriched results.
    """
    print(f"Step 3: Scoring results with LLM...")
    
    if not data["results"]:
        return {**data, "scored_results": []}
    
    scored_results = score_and_answer(
        query=data["query"],
        results=data["results"]
    )
    return {
        **data,
        "scored_results": scored_results
    }


def _filter_relevant_results(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter results to only include those above the relevance threshold.
    
    Args:
        data: Dict containing scored results.
    
    Returns:
        Dict with relevant results filtered.
    """
    print(f"Step 4: Filtering relevant results (threshold: {config.RELEVANCE_THRESHOLD})...")
    
    relevant = [
        r for r in data["scored_results"]
        if r.get("score", 0) > config.RELEVANCE_THRESHOLD
    ]
    
    print(f"  {len(relevant)}/{len(data['scored_results'])} results above threshold")
    
    return {
        **data,
        "relevant_results": relevant
    }


def _enrich_with_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich relevant results with full metadata from frame_metadata collection.
    
    Also decodes frame_image Binary back to displayable bytes.
    
    Args:
        data: Dict containing relevant results.
    
    Returns:
        Dict with fully enriched results.
    """
    print(f"Step 5: Enriching results with metadata...")
    
    enriched = []
    for result in data["relevant_results"]:
        frame_id = result.get("_id")
        
        # Fetch metadata
        metadata = get_frame_metadata(frame_id)
        
        # Create enriched result
        enriched_result = result.copy()
        
        if metadata:
            enriched_result["gps_lat"] = metadata.get("gps_lat")
            enriched_result["gps_lng"] = metadata.get("gps_lng")
            enriched_result["confidence"] = metadata.get("confidence")
            enriched_result["reid_group"] = metadata.get("reid_group")
        
        # Decode frame_image Binary to base64 for display
        if "frame_image" in enriched_result:
            frame_image = enriched_result["frame_image"]
            # Handle both Binary and bytes types
            if hasattr(frame_image, "__bytes__"):
                image_bytes = bytes(frame_image)
            else:
                image_bytes = frame_image
            
            # Store both raw bytes and base64 encoded version
            enriched_result["image_bytes"] = image_bytes
            enriched_result["image_base64"] = base64.b64encode(image_bytes).decode("utf-8")
            # Remove the Binary object as it's not JSON serializable
            del enriched_result["frame_image"]
        
        enriched.append(enriched_result)
    
    return {
        **data,
        "enriched_results": enriched
    }


def _build_timeline(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a crime timeline by sorting results by timestamp.
    
    Args:
        data: Dict containing enriched results.
    
    Returns:
        Dict with timeline added.
    """
    print(f"Step 6: Building timeline...")
    
    # Sort by timestamp ascending for chronological timeline
    timeline = sorted(
        data["enriched_results"],
        key=lambda x: (x.get("cam_id", ""), x.get("timestamp", 0))
    )
    
    # Add sequence numbers to timeline
    for i, item in enumerate(timeline):
        item["sequence"] = i + 1
    
    return {
        **data,
        "timeline": timeline
    }


def run_query(user_query: str) -> Dict[str, Any]:
    """
    Execute the complete RAG query pipeline for forensic video analysis.
    
    This function orchestrates the full query pipeline using LangChain:
    
    1. Embeds the user query using generate_embedding()
    2. Performs vector search in MongoDB to find top 10 similar frames
    3. Uses LLM to score each result for relevance (0-100)
    4. Filters to relevant results (score > 40)
    5. Enriches with full metadata (GPS, timestamps, etc.)
    6. Builds a chronological crime timeline
    
    Args:
        user_query: Natural language query describing what to find in the
            video evidence. Examples:
            - "Show me every instance of the red backpack being dropped"
            - "Find all appearances of a person in a blue jacket"
            - "When did someone enter through the back door?"
    
    Returns:
        Dict containing:
            - query (str): The original user query
            - results (List[Dict]): All enriched results sorted by relevance
            - timeline (List[Dict]): Relevant results sorted by timestamp
            - total (int): Number of relevant results found
            - summary (str): Natural language summary of findings
    
    Raises:
        ValueError: If the query is empty.
        ConnectionError: If unable to connect to required services.
        RuntimeError: If any pipeline step fails.
    
    Example:
        >>> result = run_query("Show me the red backpack being dropped")
        >>> print(f"Found {result['total']} relevant frames")
        >>> for frame in result['timeline']:
        ...     print(f"  {frame['timestamp']}s: {frame['explanation']}")
    """
    if not user_query or not user_query.strip():
        raise ValueError("Query cannot be empty")
    
    print(f"\n{'='*60}")
    print(f"QUERY: {user_query}")
    print(f"{'='*60}")
    
    # Build the LangChain pipeline using RunnableLambda
    pipeline = (
        RunnableLambda(_embed_query)
        | RunnableLambda(_vector_search_step)
        | RunnableLambda(_score_results_step)
        | RunnableLambda(_filter_relevant_results)
        | RunnableLambda(_enrich_with_metadata)
        | RunnableLambda(_build_timeline)
    )
    
    # Execute the pipeline
    result = pipeline.invoke(user_query)
    
    # Generate summary
    print(f"Step 7: Generating summary...")
    summary = generate_summary(user_query, result["enriched_results"])
    
    # Prepare final output
    output = {
        "query": user_query,
        "results": result["enriched_results"],
        "timeline": result["timeline"],
        "total": len(result["enriched_results"]),
        "summary": summary
    }
    
    print(f"\n{'='*60}")
    print(f"QUERY COMPLETE")
    print(f"{'='*60}")
    print(f"Total relevant results: {output['total']}")
    print(f"Summary: {summary}")
    
    return output


def get_frame_ids_from_results(results: Dict[str, Any]) -> List[str]:
    """
    Extract frame IDs from query results for ReID processing.
    
    Args:
        results: The output dictionary from run_query().
    
    Returns:
        List[str]: List of frame IDs from relevant results.
    """
    return [r.get("_id") for r in results.get("results", []) if r.get("_id")]


def format_results_for_display(results: Dict[str, Any], include_images: bool = False) -> Dict[str, Any]:
    """
    Format results for JSON serialization and display.
    
    Removes non-serializable fields and optionally removes large image data.
    
    Args:
        results: The output dictionary from run_query().
        include_images: If True, include base64 images; if False, exclude them.
    
    Returns:
        Dict: JSON-serializable results dictionary.
    """
    output = results.copy()
    
    def clean_result(r):
        cleaned = {
            "_id": r.get("_id"),
            "cam_id": r.get("cam_id"),
            "timestamp": r.get("timestamp"),
            "score": r.get("score"),
            "relevant": r.get("relevant"),
            "explanation": r.get("explanation"),
            "caption": r.get("caption"),
            "gdrive_url": r.get("gdrive_url"),
            "gps_lat": r.get("gps_lat"),
            "gps_lng": r.get("gps_lng"),
            "reid_group": r.get("reid_group"),
            "sequence": r.get("sequence")
        }
        if include_images:
            cleaned["image_base64"] = r.get("image_base64")
        return cleaned
    
    output["results"] = [clean_result(r) for r in output.get("results", [])]
    output["timeline"] = [clean_result(r) for r in output.get("timeline", [])]
    
    return output
