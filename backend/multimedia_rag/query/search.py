"""
Vector search module for querying frame embeddings in MongoDB Atlas.

This module provides functionality to perform semantic similarity search
on the frame_embeddings collection using MongoDB Atlas Vector Search.
Results are ranked by similarity to the query embedding.

Prerequisites:
    A MongoDB Atlas Vector Search index named "embedding_index" must be
    created on the frame_embeddings collection with the following configuration:
    
    {
        "name": "embedding_index",
        "type": "vectorSearch",
        "definition": {
            "fields": [{
                "type": "vector",
                "path": "embedding",
                "numDimensions": 384,
                "similarity": "cosine"
            }]
        }
    }

Functions:
    vector_search: Perform vector similarity search on frame embeddings
"""

from typing import List, Dict, Any, Optional

from pymongo.errors import PyMongoError, OperationFailure

from multimedia_rag.ingestion.mongo_store import get_db
from multimedia_rag import config


def vector_search(
    query_embedding: List[float],
    top_k: int = None,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search on the frame_embeddings collection.
    
    This function uses MongoDB Atlas Vector Search to find frames whose
    caption embeddings are most similar to the query embedding. Results
    are returned sorted by similarity score (highest first).
    
    Args:
        query_embedding: A 384-dimensional embedding vector representing
            the search query. Should be generated using the same embedding
            model used during ingestion (all-MiniLM-L6-v2).
        top_k: Maximum number of results to return. Defaults to
            config.TOP_K_RESULTS (10).
        filter_dict: Optional MongoDB filter to apply to results.
            Example: {"cam_id": "cam1"} to search only camera 1.
    
    Returns:
        List[Dict]: A list of result dictionaries, each containing:
            - _id (str): Frame identifier
            - caption (str): Frame caption text
            - cam_id (str): Camera identifier
            - timestamp (int): Second in the video
            - frame_image (Binary): JPEG image bytes
            - gdrive_url (str): Google Drive URL of source video
            - score (float): Similarity score (0-1, higher is more similar)
    
    Raises:
        ValueError: If the query embedding is invalid.
        OperationFailure: If the vector search index doesn't exist or query fails.
        PyMongoError: If database operation fails.
    
    Example:
        >>> from ingestion.embedder import generate_embedding
        >>> query_emb = generate_embedding("person with red backpack")
        >>> results = vector_search(query_emb, top_k=5)
        >>> for r in results:
        ...     print(f"{r['_id']}: {r['score']:.4f} - {r['caption'][:50]}...")
        cam1_t0142: 0.8934 - A person wearing a red jacket carrying a backpack...
    """
    # Validate embedding
    if not query_embedding:
        raise ValueError("Query embedding cannot be empty")
    
    if len(query_embedding) != config.EMBEDDING_DIMENSION:
        raise ValueError(
            f"Query embedding must be {config.EMBEDDING_DIMENSION} dimensions, "
            f"got {len(query_embedding)}"
        )
    
    # Use default top_k if not specified
    if top_k is None:
        top_k = config.TOP_K_RESULTS
    
    try:
        db = get_db()
        collection = db[config.COLLECTION_FRAME_EMBEDDINGS]
        
        # Build the $vectorSearch aggregation stage
        vector_search_stage = {
            "$vectorSearch": {
                "index": config.VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": config.NUM_CANDIDATES,
                "limit": top_k
            }
        }
        
        # Add filter if provided
        if filter_dict:
            vector_search_stage["$vectorSearch"]["filter"] = filter_dict
        
        # Build the aggregation pipeline
        pipeline = [
            vector_search_stage,
            {
                "$project": {
                    "_id": 1,
                    "caption": 1,
                    "cam_id": 1,
                    "timestamp": 1,
                    "frame_image": 1,
                    "gdrive_url": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        # Execute the aggregation
        results = list(collection.aggregate(pipeline))
        
        print(f"Vector search returned {len(results)} results")
        
        return results
        
    except OperationFailure as e:
        # Check if it's an index not found error
        error_msg = str(e)
        if "index not found" in error_msg.lower() or "no such index" in error_msg.lower():
            raise OperationFailure(
                f"Vector search index '{config.VECTOR_INDEX_NAME}' not found. "
                "Please create the index in MongoDB Atlas:\n"
                "1. Go to your MongoDB Atlas cluster\n"
                "2. Navigate to Search Indexes\n"
                "3. Create a new Vector Search index with:\n"
                f"   - Index name: {config.VECTOR_INDEX_NAME}\n"
                f"   - Collection: {config.COLLECTION_FRAME_EMBEDDINGS}\n"
                "   - Path: embedding\n"
                "   - Dimensions: 384\n"
                "   - Similarity: cosine"
            )
        raise OperationFailure(f"Vector search failed: {str(e)}")
    except PyMongoError as e:
        raise PyMongoError(f"Database error during vector search: {str(e)}")


def search_by_camera(
    query_embedding: List[float],
    cam_id: str,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Perform vector search filtered to a specific camera.
    
    Args:
        query_embedding: The query embedding vector.
        cam_id: Camera identifier to filter results.
        top_k: Maximum number of results.
    
    Returns:
        List[Dict]: Search results from the specified camera only.
    """
    return vector_search(
        query_embedding=query_embedding,
        top_k=top_k,
        filter_dict={"cam_id": cam_id}
    )


def search_by_time_range(
    query_embedding: List[float],
    start_ts: int,
    end_ts: int,
    top_k: int = None
) -> List[Dict[str, Any]]:
    """
    Perform vector search filtered to a specific time range.
    
    Args:
        query_embedding: The query embedding vector.
        start_ts: Start timestamp (inclusive).
        end_ts: End timestamp (inclusive).
        top_k: Maximum number of results.
    
    Returns:
        List[Dict]: Search results within the specified time range.
    """
    return vector_search(
        query_embedding=query_embedding,
        top_k=top_k,
        filter_dict={
            "timestamp": {
                "$gte": start_ts,
                "$lte": end_ts
            }
        }
    )


def get_vector_search_index_info() -> Dict[str, Any]:
    """
    Get information about the vector search index status.
    
    Returns:
        Dict: Index information or error details.
    """
    try:
        db = get_db()
        collection = db[config.COLLECTION_FRAME_EMBEDDINGS]
        
        # List all search indexes
        indexes = list(collection.list_search_indexes())
        
        for index in indexes:
            if index.get('name') == config.VECTOR_INDEX_NAME:
                return {
                    'exists': True,
                    'name': index.get('name'),
                    'status': index.get('status', 'unknown'),
                    'queryable': index.get('queryable', False)
                }
        
        return {
            'exists': False,
            'message': f"Index '{config.VECTOR_INDEX_NAME}' not found"
        }
        
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }
