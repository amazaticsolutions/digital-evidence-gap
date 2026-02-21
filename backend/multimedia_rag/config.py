"""
Configuration module for the Multimedia RAG Engine.

This module centralizes all configuration constants and environment variables
used throughout the application. It loads sensitive credentials from the .env
file in the backend directory and provides constants for MongoDB collections, 
Ollama models, and processing parameters.

Environment Variables Required (in backend/.env):
    MONGO_INITDB_DATABASE: MongoDB Atlas connection string
    GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH: Path to Google service account JSON file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env (parent directory)
_backend_dir = Path(__file__).resolve().parent.parent
_env_path = _backend_dir / ".env"
load_dotenv(_env_path)

# =============================================================================
# MongoDB Configuration
# =============================================================================

# MongoDB Atlas connection URI (loaded from backend's .env)
# Supports both MONGODB_URI (preferred) and legacy MONGO_INITDB_DATABASE
MONGODB_URI: str = os.getenv("MONGODB_URI", "") or os.getenv("MONGO_INITDB_DATABASE", "")

# Database name for storing all evidence data
MONGODB_DB_NAME: str = "evidence_db"

# Collection names
COLLECTION_FRAME_EMBEDDINGS: str = "frame_embeddings"
COLLECTION_FRAME_METADATA: str = "frame_metadata"
COLLECTION_REID_TRACKS: str = "reid_tracks"

# Vector search index name (must be created in MongoDB Atlas)
VECTOR_INDEX_NAME: str = "embedding_index"

# =============================================================================
# Ollama Configuration
# =============================================================================

# Base URL for Ollama API (local installation)
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# LLaVA model for vision tasks (frame captioning)
LLAVA_MODEL: str = "llava"

# LLM model for text tasks (scoring and answering queries)
LLM_MODEL: str = "llama3"

# =============================================================================
# Embedding Configuration
# =============================================================================

# Sentence Transformer model for text embeddings
# all-MiniLM-L6-v2 produces 384-dimensional vectors
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# Dimensionality of the embedding vectors
EMBEDDING_DIMENSION: int = 384

# =============================================================================
# Video Processing Configuration
# =============================================================================

# Frame extraction rate (frames per second)
# 1 = extract 1 frame every second
FRAME_RATE: int = 1

# Frame resize dimensions for processing
FRAME_WIDTH: int = 640
FRAME_HEIGHT: int = 480

# Temporary directory for video downloads
TEMP_VIDEO_DIR: str = "/tmp/videos"

# =============================================================================
# Query Configuration
# =============================================================================

# Number of top results to return from vector search
TOP_K_RESULTS: int = 10

# Number of candidate vectors for approximate nearest neighbor search
NUM_CANDIDATES: int = 100

# Minimum relevance score (0-100) for a result to be considered relevant
RELEVANCE_THRESHOLD: int = 40

# =============================================================================
# Re-identification Configuration
# =============================================================================

# Cosine similarity threshold for grouping as same person
REID_SIMILARITY_THRESHOLD: float = 0.7

# torchreid model architecture
REID_MODEL: str = "osnet_x1_0"

# =============================================================================
# Google Drive Configuration
# =============================================================================

# Path to Google service account credentials file
# Maps to GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH in backend/.env
GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH", "")

# Google Drive folder ID for video storage (optional)
# Maps to GOOGLE_DRIVE_FOLDER_ID in backend/.env
GDRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

# =============================================================================
# Validation
# =============================================================================

def validate_config() -> bool:
    """
    Validate that all required configuration values are set.
    
    Returns:
        bool: True if all required configs are valid, raises ValueError otherwise.
    
    Raises:
        ValueError: If any required configuration is missing or invalid.
    """
    errors = []
    
    if not MONGODB_URI:
        errors.append("MONGODB_URI environment variable is not set in backend/.env")
    
    if not GOOGLE_CREDENTIALS_PATH:
        errors.append("GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH environment variable is not set in backend/.env")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# Ensure temp directory exists
os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
