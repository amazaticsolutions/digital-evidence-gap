"""
MongoDB storage module for frame data and metadata.

This module provides functionality to store and retrieve frame embeddings,
captions, images, and metadata in MongoDB Atlas. The database connection
is established once at module import and reused for all operations.

Collections:
    - frame_embeddings: Stores embeddings, captions, and frame images
    - frame_metadata: Stores GPS coordinates, confidence scores, and ReID groups
    - reid_tracks: Stores person tracking data across cameras

Functions:
    store_frame: Store frame data in both collections
    check_frame_exists: Check if a frame has already been processed
    get_db: Get the database connection
"""

from typing import Optional, Dict, Any, List
from bson import Binary
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError, ConnectionFailure

from multimedia_rag import config


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
                connectTimeoutMS=10000
            )
            # Test the connection
            _client.admin.command('ping')
            print(f"Connected to MongoDB Atlas")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
    
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
    
    This function inserts the frame embedding, caption, and image into the
    frame_embeddings collection, and inserts metadata (GPS, timestamps) into
    the frame_metadata collection. Both operations use the same _id.
    
    Args:
        frame_data: Dictionary containing all frame information:
            - _id (str): Unique frame identifier (e.g., "cam1_t0001")
            - cam_id (str): Camera identifier
            - timestamp (int): Second in the video
            - embedding (List[float]): 384-dimensional caption embedding
            - caption (str): Text description of the frame
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
        ...     'embedding': [0.1, 0.2, ...],  # 384 floats
        ...     'caption': 'A person walking...',
        ...     'frame_image': Binary(jpeg_bytes),
        ...     'gdrive_url': 'https://drive.google.com/...',
        ...     'gps_lat': 40.7128,
        ...     'gps_lng': -74.0060
        ... })
    """
    # Validate required fields
    required_embedding_fields = ['_id', 'embedding', 'caption', 'cam_id', 
                                  'timestamp', 'frame_image', 'gdrive_url']
    required_metadata_fields = ['_id', 'cam_id', 'timestamp', 'gps_lat', 
                                 'gps_lng', 'gdrive_url']
    
    for field in required_embedding_fields:
        if field not in frame_data:
            raise ValueError(f"Missing required field: {field}")
    
    for field in required_metadata_fields:
        if field not in frame_data:
            raise ValueError(f"Missing required field: {field}")
    
    try:
        # Prepare frame_embeddings document
        embedding_doc = {
            '_id': frame_data['_id'],
            'embedding': frame_data['embedding'],
            'caption': frame_data['caption'],
            'cam_id': frame_data['cam_id'],
            'timestamp': frame_data['timestamp'],
            'frame_image': frame_data['frame_image'],
            'gdrive_url': frame_data['gdrive_url']
        }
        
        # Prepare frame_metadata document
        metadata_doc = {
            '_id': frame_data['_id'],
            'cam_id': frame_data['cam_id'],
            'timestamp': frame_data['timestamp'],
            'gps_lat': frame_data['gps_lat'],
            'gps_lng': frame_data['gps_lng'],
            'gdrive_url': frame_data['gdrive_url'],
            'confidence': None,  # Set when query runs
            'reid_group': None   # Set when re-id runs
        }
        
        # Get collections
        embeddings_col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        metadata_col = get_collection(config.COLLECTION_FRAME_METADATA)
        
        # Insert into frame_embeddings collection
        try:
            embeddings_col.insert_one(embedding_doc)
        except DuplicateKeyError:
            # Frame already exists, skip
            print(f"  Frame {frame_data['_id']} already exists in embeddings, skipping")
            return
        
        # Insert into frame_metadata collection
        try:
            metadata_col.insert_one(metadata_doc)
        except DuplicateKeyError:
            # Metadata already exists (shouldn't happen if above succeeded)
            print(f"  Metadata for {frame_data['_id']} already exists")
            
    except PyMongoError as e:
        raise PyMongoError(f"Failed to store frame {frame_data.get('_id', 'unknown')}: {str(e)}")


def check_frame_exists(frame_id: str) -> bool:
    """
    Check if a frame has already been processed and stored.
    
    This function is used to skip already processed frames on re-runs,
    allowing for incremental ingestion of new frames.
    
    Args:
        frame_id: The unique frame identifier (e.g., "cam1_t0001").
    
    Returns:
        bool: True if the frame exists in frame_embeddings, False otherwise.
    
    Raises:
        PyMongoError: If database query fails.
    
    Example:
        >>> check_frame_exists('cam1_t0001')
        True
        >>> check_frame_exists('cam1_t9999')
        False
    """
    try:
        embeddings_col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        result = embeddings_col.find_one({'_id': frame_id}, {'_id': 1})
        return result is not None
    except PyMongoError as e:
        raise PyMongoError(f"Failed to check frame existence: {str(e)}")


def get_frame_metadata(frame_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve metadata for a specific frame.
    
    Args:
        frame_id: The unique frame identifier.
    
    Returns:
        Optional[Dict]: The metadata document, or None if not found.
    
    Raises:
        PyMongoError: If database query fails.
    """
    try:
        metadata_col = get_collection(config.COLLECTION_FRAME_METADATA)
        return metadata_col.find_one({'_id': frame_id})
    except PyMongoError as e:
        raise PyMongoError(f"Failed to get frame metadata: {str(e)}")


def get_frame_embedding_doc(frame_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the full embedding document for a specific frame.
    
    Args:
        frame_id: The unique frame identifier.
    
    Returns:
        Optional[Dict]: The embedding document including image, or None if not found.
    
    Raises:
        PyMongoError: If database query fails.
    """
    try:
        embeddings_col = get_collection(config.COLLECTION_FRAME_EMBEDDINGS)
        return embeddings_col.find_one({'_id': frame_id})
    except PyMongoError as e:
        raise PyMongoError(f"Failed to get frame embedding document: {str(e)}")


def update_frame_metadata(frame_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update metadata fields for a specific frame.
    
    Used to set confidence scores after queries and reid_group after
    person re-identification.
    
    Args:
        frame_id: The unique frame identifier.
        updates: Dictionary of fields to update (e.g., {'confidence': 0.95}).
    
    Returns:
        bool: True if a document was updated, False if frame not found.
    
    Raises:
        PyMongoError: If database update fails.
    """
    try:
        metadata_col = get_collection(config.COLLECTION_FRAME_METADATA)
        result = metadata_col.update_one(
            {'_id': frame_id},
            {'$set': updates}
        )
        return result.modified_count > 0
    except PyMongoError as e:
        raise PyMongoError(f"Failed to update frame metadata: {str(e)}")


def store_reid_track(person_id: str, appearances: List[Dict[str, Any]]) -> None:
    """
    Store or update a person's track across cameras.
    
    Args:
        person_id: Unique person identifier (e.g., "Person_A").
        appearances: List of appearance dictionaries, each containing:
            - cam (str): Camera ID
            - ts (int): Timestamp
            - frame_id (str): Frame identifier
    
    Raises:
        PyMongoError: If database operation fails.
    """
    try:
        tracks_col = get_collection(config.COLLECTION_REID_TRACKS)
        
        # Upsert the track document
        tracks_col.update_one(
            {'person_id': person_id},
            {'$set': {
                'person_id': person_id,
                'appearances': appearances
            }},
            upsert=True
        )
    except PyMongoError as e:
        raise PyMongoError(f"Failed to store reid track: {str(e)}")


def get_reid_tracks() -> List[Dict[str, Any]]:
    """
    Retrieve all person re-identification tracks.
    
    Returns:
        List[Dict]: List of all reid_tracks documents.
    
    Raises:
        PyMongoError: If database query fails.
    """
    try:
        tracks_col = get_collection(config.COLLECTION_REID_TRACKS)
        return list(tracks_col.find({}))
    except PyMongoError as e:
        raise PyMongoError(f"Failed to get reid tracks: {str(e)}")


def close_connection() -> None:
    """
    Close the MongoDB connection.
    
    Call this when shutting down the application to cleanly close
    the database connection.
    """
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        print("MongoDB connection closed")
