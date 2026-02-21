"""
MongoDB storage module for frame data and metadata.

This module provides functionality to store and retrieve frame embeddings,
captions, images, and metadata in MongoDB Atlas. The database connection
is established once at module import and reused for all operations.

The schema stores THREE embeddings and THREE captions per frame to support
multi-index vector search (brief / detailed / regional).

Collections:
    - frame_embeddings: Stores embeddings, captions, and frame images
    - frame_metadata: Stores GPS coordinates, confidence scores, and ReID groups
    - reid_tracks: Stores person tracking data across cameras

Functions:
    store_frame: Store frame data in both collections
    check_frame_exists: Check if a frame has already been processed
    get_db: Get the database connection
    setup_indexes: Print instructions for creating Atlas vector search indexes
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from bson import Binary
from pymongo import MongoClient, TEXT
from pymongo.errors import DuplicateKeyError, PyMongoError, ConnectionFailure

from multimedia_rag import config

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# =============================================================================
# Module-level database connection (established once, reused for all calls)
# =============================================================================

_client: Optional[MongoClient] = None
_db = None


def _get_client() -> MongoClient:
    """
    Get or create the MongoDB client connection.

    Returns:
        MongoClient: The MongoDB client instance.

    Raises:
        ConnectionError: If unable to connect to MongoDB.
    """
    global _client

    if _client is None:
        if not config.MONGODB_URI:
            raise ValueError(
                "MONGODB_URI environment variable is not set. "
                "Please set it in your .env file."
            )
        try:
            _client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
            )
            _client.admin.command("ping")
            _log("Connected to MongoDB Atlas")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    return _client


def get_db():
    """
    Get the database instance.

    Returns:
        Database: The MongoDB database instance for evidence_db.

    Raises:
        ConnectionError: If unable to connect to MongoDB.
    """
    global _db

    if _db is None:
        client = _get_client()
        _db = client[config.MONGODB_DB_NAME]

    return _db


def get_collection(collection_name: str):
    """
    Get a specific collection from the database.

    Args:
        collection_name: Name of the collection to retrieve.

    Returns:
        Collection: The MongoDB collection instance.
    """
    db = get_db()
    return db[collection_name]


def store_frame(frame_data: Dict[str, Any]) -> None:
    """
    Store frame data in both frame_embeddings and frame_metadata collections.

    The frame_embeddings document now stores three captions and three
    embeddings (brief / detailed / regional) to support multi-index vector
    search.

    Args:
        frame_data: Dictionary containing all frame information:
            - _id (str): Unique frame identifier (e.g. "cam1_t0001")
            - cam_id (str): Camera identifier
            - timestamp (int): Second in the video
            - caption_brief (str): Brief caption
            - caption_detailed (str): Detailed caption
            - caption_regional (str): Regional caption
            - embedding_brief (List[float]): 384-dim embedding of brief caption
            - embedding_detailed (List[float]): 384-dim embedding of detailed caption
            - embedding_regional (List[float]): 384-dim embedding of regional caption
            - frame_image (Binary): JPEG image bytes as MongoDB Binary
            - gdrive_url (str): Google Drive URL of source video
            - gps_lat (float): GPS latitude coordinate
            - gps_lng (float): GPS longitude coordinate

    Raises:
        ValueError: If required fields are missing from frame_data.
        PyMongoError: If database operation fails.

    Example:
        >>> from bson import Binary
        >>> store_frame({
        ...     '_id': 'cam1_t0001',
        ...     'cam_id': 'cam1',
        ...     'timestamp': 1,
        ...     'caption_brief': 'Man near bin',
        ...     'caption_detailed': 'Man in red jacket near blue bin',
        ...     'caption_regional': 'Center: man bending. Right: blue bin',
        ...     'embedding_brief': [0.1, ...],
        ...     'embedding_detailed': [0.2, ...],
        ...     'embedding_regional': [0.3, ...],
        ...     'frame_image': Binary(jpeg_bytes),
        ...     'gdrive_url': 'https://drive.google.com/...',
        ...     'gps_lat': 40.7128,
        ...     'gps_lng': -74.0060
        ... })
    """
    required_embedding_fields = [
        "_id", "cam_id", "timestamp",
        "caption_brief", "caption_detailed", "caption_regional",
        "embedding_brief", "embedding_detailed", "embedding_regional",
        "frame_image", "gdrive_url",
    ]
    required_metadata_fields = [
        "_id", "cam_id", "timestamp", "gps_lat", "gps_lng", "gdrive_url",
    ]

    for field in required_embedding_fields:
        if field not in frame_data:
            raise ValueError(f"Missing required field: {field}")
    for field in required_metadata_fields:
        if field not in frame_data:
            raise ValueError(f"Missing required field: {field}")

    try:
        # Prepare frame_embeddings document (three captions + three embeddings)
        embedding_doc = {
            "_id": frame_data["_id"],
            "caption_brief": frame_data["caption_brief"],
            "caption_detailed": frame_data["caption_detailed"],
            "caption_regional": frame_data["caption_regional"],
            "embedding_brief": frame_data["embedding_brief"],
            "embedding_detailed": frame_data["embedding_detailed"],
            "embedding_regional": frame_data["embedding_regional"],
            "cam_id": frame_data["cam_id"],
            "timestamp": frame_data["timestamp"],
            "frame_image": frame_data["frame_image"],
            "gdrive_url": frame_data["gdrive_url"],
        }

        # Prepare frame_metadata document
        metadata_doc = {
            "_id": frame_data["_id"],
            "cam_id": frame_data["cam_id"],
            "timestamp": frame_data["timestamp"],
            "gps_lat": frame_data["gps_lat"],
            "gps_lng": frame_data["gps_lng"],
            "gdrive_url": frame_data["gdrive_url"],
            "confidence": None,
            "reid_group": None,
        }

        embeddings_col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        metadata_col = get_collection(config.COLLECTION_FRAME_METADATA)

        # Insert into frame_embeddings collection
        try:
            embeddings_col.insert_one(embedding_doc)
        except DuplicateKeyError:
            _log(f"  Frame {frame_data['_id']} already exists in embeddings, skipping")
            return

        # Insert into frame_metadata collection
        try:
            metadata_col.insert_one(metadata_doc)
        except DuplicateKeyError:
            _log(f"  Metadata for {frame_data['_id']} already exists")

    except PyMongoError as e:
        _log(f"ERROR storing frame {frame_data.get('_id', 'unknown')}: {e}")
        raise PyMongoError(
            f"Failed to store frame {frame_data.get('_id', 'unknown')}: {e}"
        )


def check_frame_exists(frame_id: str) -> bool:
    """
    Check if a frame has already been processed and stored.

    Args:
        frame_id: The unique frame identifier (e.g. "cam1_t0001").

    Returns:
        bool: True if the frame exists in frame_embeddings, False otherwise.
    """
    try:
        embeddings_col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        result = embeddings_col.find_one({"_id": frame_id}, {"_id": 1})
        return result is not None
    except PyMongoError as e:
        _log(f"ERROR checking frame existence: {e}")
        return False


def get_frame_metadata(frame_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a specific frame.

    Args:
        frame_id: The unique frame identifier.

    Returns:
        Optional[Dict]: The metadata document, or None if not found.
    """
    try:
        metadata_col = get_collection(config.COLLECTION_FRAME_METADATA)
        return metadata_col.find_one({"_id": frame_id})
    except PyMongoError as e:
        _log(f"ERROR getting frame metadata: {e}")
        return None


def get_frame_embedding_doc(frame_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the full embedding document for a specific frame.

    Args:
        frame_id: The unique frame identifier.

    Returns:
        Optional[Dict]: The embedding document including image, or None.
    """
    try:
        embeddings_col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        return embeddings_col.find_one({"_id": frame_id})
    except PyMongoError as e:
        _log(f"ERROR getting frame embedding doc: {e}")
        return None


def update_frame_metadata(frame_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update metadata fields for a specific frame.

    Args:
        frame_id: The unique frame identifier.
        updates: Dictionary of fields to update.

    Returns:
        bool: True if a document was updated, False if not found.
    """
    try:
        metadata_col = get_collection(config.COLLECTION_FRAME_METADATA)
        result = metadata_col.update_one({"_id": frame_id}, {"$set": updates})
        return result.modified_count > 0
    except PyMongoError as e:
        _log(f"ERROR updating frame metadata: {e}")
        return False


def store_reid_track(person_id: str, appearances: List[Dict[str, Any]]) -> None:
    """
    Store or update a person's track across cameras.

    Args:
        person_id: Unique person identifier (e.g. "Person_A").
        appearances: List of appearance dictionaries with cam, ts, frame_id.
    """
    try:
        tracks_col = get_collection(config.COLLECTION_REID_TRACKS)
        tracks_col.update_one(
            {"person_id": person_id},
            {"$set": {"person_id": person_id, "appearances": appearances}},
            upsert=True,
        )
    except PyMongoError as e:
        _log(f"ERROR storing reid track: {e}")


def get_reid_tracks() -> List[Dict[str, Any]]:
    """
    Retrieve all person re-identification tracks.

    Returns:
        List[Dict]: List of all reid_tracks documents.
    """
    try:
        tracks_col = get_collection(config.COLLECTION_REID_TRACKS)
        return list(tracks_col.find({}))
    except PyMongoError as e:
        _log(f"ERROR getting reid tracks: {e}")
        return []


def ensure_text_index() -> None:
    """
    Create a compound text index on the three caption fields for keyword
    fallback search.  Safe to call multiple times — MongoDB ignores
    duplicate index creation.
    """
    try:
        col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        col.create_index(
            [
                ("caption_brief", TEXT),
                ("caption_detailed", TEXT),
                ("caption_regional", TEXT),
            ],
            name="caption_text_index",
        )
        _log("Text index 'caption_text_index' ensured on frame_embeddings")
    except PyMongoError as e:
        _log(f"WARNING: Could not create text index: {e}")


def setup_indexes() -> None:
    """
    Print instructions for creating the three MongoDB Atlas Vector Search
    indexes required by the improved multi-index pipeline.

    The indexes must be created manually in the Atlas UI because the
    ``createSearchIndex`` command requires an M10+ cluster.
    """
    _log("=" * 70)
    _log("MONGODB ATLAS VECTOR SEARCH INDEX SETUP")
    _log("=" * 70)
    _log("")
    _log("Create the following THREE vector search indexes in the Atlas UI")
    _log(f"on collection: {config.MONGODB_DB_NAME}.{config.COLLECTION_FRAME_EMBEDDINGS}")
    _log("")

    indexes = [
        ("embedding_brief_index", "embedding_brief"),
        ("embedding_detailed_index", "embedding_detailed"),
        ("embedding_regional_index", "embedding_regional"),
    ]

    for idx_name, field in indexes:
        _log(f"  Index name : {idx_name}")
        _log(f"  Field path : {field}")
        _log(f"  Dimensions : {config.EMBEDDING_DIMENSION}")
        _log(f"  Similarity : cosine")
        _log(f"  JSON definition:")
        _log(f'    {{')
        _log(f'      "name": "{idx_name}",')
        _log(f'      "type": "vectorSearch",')
        _log(f'      "definition": {{')
        _log(f'        "fields": [{{')
        _log(f'          "type": "vector",')
        _log(f'          "path": "{field}",')
        _log(f'          "numDimensions": {config.EMBEDDING_DIMENSION},')
        _log(f'          "similarity": "cosine"')
        _log(f'        }}]')
        _log(f'      }}')
        _log(f'    }}')
        _log("")

    _log("Also ensure a TEXT index exists for keyword fallback search:")
    _log("  db.frame_embeddings.createIndex({")
    _log('    caption_brief:    "text",')
    _log('    caption_detailed: "text",')
    _log('    caption_regional: "text"')
    _log("  })")
    _log("")

    # Attempt to create the text index programmatically
    ensure_text_index()


def close_connection() -> None:
    """
    Close the MongoDB connection.
    """
    global _client, _db

    if _client is not None:
        _client.close()
        _client = None
        _db = None
        _log("MongoDB connection closed")
