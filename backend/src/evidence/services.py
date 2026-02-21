"""
Evidence services for video upload and processing.

This module provides business logic for:
- Uploading videos to local storage
- Uploading videos to Google Drive (via user OAuth)
- Managing video evidence records
- Triggering RAG pipeline processing
"""

import os
import uuid
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, BinaryIO

from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

from .models import VideoEvidence, ProcessingJob


# =============================================================================
# Configuration
# =============================================================================

# Video upload directory (relative to backend)
UPLOAD_DIR = Path(settings.BASE_DIR) / "uploads" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed video MIME types
ALLOWED_MIME_TYPES = {
    'video/mp4',
    'video/avi',
    'video/mov',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
    'video/x-matroska',
}

# Max file size (500MB)
MAX_FILE_SIZE = 500 * 1024 * 1024


# =============================================================================
# Database Connection
# =============================================================================

def _get_db():
    """Get MongoDB database connection."""
    mongo_uri = os.getenv("MONGO_INITDB_DATABASE", "")
    if not mongo_uri:
        raise ValueError("MONGO_INITDB_DATABASE not configured")
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return client["evidence_db"]


# =============================================================================
# Video Upload Services
# =============================================================================

def validate_video_file(file) -> Tuple[bool, str]:
    """
    Validate an uploaded video file.
    
    Args:
        file: Django UploadedFile object
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if file.size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Check MIME type
    content_type = file.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        return False, f"Invalid file type: {content_type}. Allowed types: mp4, avi, mov, webm, mkv"
    
    return True, ""


def get_video_duration(file_path: str) -> Optional[float]:
    """
    Get video duration using ffprobe.
    
    Args:
        file_path: Path to the video file
    
    Returns:
        Duration in seconds, or None if unable to determine
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def upload_video_local(
    file,
    cam_id: str,
    gps_lat: float = 0.0,
    gps_lng: float = 0.0,
    case_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Upload a video file to local storage and create database record.
    
    Args:
        file: Django UploadedFile object
        cam_id: Camera identifier
        gps_lat: GPS latitude
        gps_lng: GPS longitude
        case_id: Associated case ID
        metadata: Additional metadata
    
    Returns:
        Dict containing upload result with video_id and details
    
    Raises:
        ValueError: If validation fails
        IOError: If file save fails
        PyMongoError: If database operation fails
    """
    # Validate file
    is_valid, error_msg = validate_video_file(file)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Generate unique filename
    file_ext = Path(file.name).suffix.lower()
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # Save file to disk
        with open(file_path, 'wb') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
        
        # Get video duration
        duration = get_video_duration(str(file_path))
        
        # Create database record
        doc = VideoEvidence.create_document(
            filename=file.name,
            cam_id=cam_id,
            file_size=file.size,
            storage_type=VideoEvidence.STORAGE_LOCAL,
            local_path=str(file_path),
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            case_id=case_id,
            duration=duration,
            metadata=metadata
        )
        
        db = _get_db()
        result = db[VideoEvidence.COLLECTION_NAME].insert_one(doc)
        video_id = str(result.inserted_id)
        
        return {
            "success": True,
            "video_id": video_id,
            "filename": file.name,
            "file_size": file.size,
            "duration": duration,
            "storage_type": "local",
            "local_path": str(file_path),
            "status": VideoEvidence.STATUS_PENDING
        }
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise


def upload_video_gdrive_link(
    gdrive_url: str,
    cam_id: str,
    gps_lat: float = 0.0,
    gps_lng: float = 0.0,
    case_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Register a Google Drive video link for processing.
    
    Since service accounts can't upload to personal Drive, users can
    manually upload videos to Drive and provide the link here.
    
    Args:
        gdrive_url: Google Drive URL or file ID
        cam_id: Camera identifier
        gps_lat: GPS latitude
        gps_lng: GPS longitude
        case_id: Associated case ID
        metadata: Additional metadata
    
    Returns:
        Dict containing registration result
    """
    import re
    
    # Extract file ID from URL
    file_id = gdrive_url
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', gdrive_url)
    if match:
        file_id = match.group(1)
    else:
        match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', gdrive_url)
        if match:
            file_id = match.group(1)
    
    # Verify file is accessible
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        creds_path = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH')
        if creds_path:
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=creds)
            
            file_info = service.files().get(
                fileId=file_id,
                fields='id,name,size,mimeType'
            ).execute()
            
            filename = file_info.get('name', 'unknown.mp4')
            file_size = int(file_info.get('size', 0))
        else:
            filename = f"gdrive_{file_id}.mp4"
            file_size = 0
    except Exception as e:
        raise ValueError(f"Cannot access Google Drive file: {str(e)}")
    
    # Create database record
    gdrive_view_url = f"https://drive.google.com/file/d/{file_id}/view"
    
    doc = VideoEvidence.create_document(
        filename=filename,
        cam_id=cam_id,
        file_size=file_size,
        storage_type=VideoEvidence.STORAGE_GDRIVE,
        gdrive_file_id=file_id,
        gdrive_url=gdrive_view_url,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        case_id=case_id,
        metadata=metadata
    )
    
    db = _get_db()
    result = db[VideoEvidence.COLLECTION_NAME].insert_one(doc)
    video_id = str(result.inserted_id)
    
    return {
        "success": True,
        "video_id": video_id,
        "filename": filename,
        "file_size": file_size,
        "storage_type": "gdrive",
        "gdrive_file_id": file_id,
        "gdrive_url": gdrive_view_url,
        "status": VideoEvidence.STATUS_PENDING
    }


# =============================================================================
# Video Management Services
# =============================================================================

def get_video(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get video evidence by ID.
    
    Args:
        video_id: Video document ID
    
    Returns:
        Video document dict or None
    """
    try:
        db = _get_db()
        doc = db[VideoEvidence.COLLECTION_NAME].find_one({"_id": ObjectId(video_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except Exception:
        return None


def list_videos(
    case_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> Dict[str, Any]:
    """
    List video evidence with optional filters.
    
    Args:
        case_id: Filter by case ID
        status: Filter by processing status
        limit: Maximum results
        skip: Offset for pagination
    
    Returns:
        Dict with videos list and total count
    """
    db = _get_db()
    collection = db[VideoEvidence.COLLECTION_NAME]
    
    # Build filter
    query = {}
    if case_id:
        query["case_id"] = case_id
    if status:
        query["status"] = status
    
    # Get total count
    total = collection.count_documents(query)
    
    # Get videos
    cursor = collection.find(query).sort("upload_date", -1).skip(skip).limit(limit)
    videos = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        videos.append(doc)
    
    return {
        "videos": videos,
        "total": total,
        "limit": limit,
        "skip": skip
    }


def delete_video(video_id: str) -> bool:
    """
    Delete a video evidence record and its file.
    
    Args:
        video_id: Video document ID
    
    Returns:
        True if deleted, False if not found
    """
    db = _get_db()
    
    # Get video to find file path
    doc = db[VideoEvidence.COLLECTION_NAME].find_one({"_id": ObjectId(video_id)})
    if not doc:
        return False
    
    # Delete local file if exists
    if doc.get("storage_type") == VideoEvidence.STORAGE_LOCAL:
        local_path = doc.get("local_path")
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
    
    # Delete database record
    result = db[VideoEvidence.COLLECTION_NAME].delete_one({"_id": ObjectId(video_id)})
    return result.deleted_count > 0


def update_video_status(
    video_id: str,
    status: str,
    frames_processed: int = 0,
    error_message: Optional[str] = None
) -> bool:
    """
    Update video processing status.
    
    Args:
        video_id: Video document ID
        status: New status
        frames_processed: Number of frames processed
        error_message: Error message if failed
    
    Returns:
        True if updated
    """
    db = _get_db()
    
    update = {
        "$set": {
            "status": status,
            "frames_processed": frames_processed
        }
    }
    
    if error_message:
        update["$set"]["error_message"] = error_message
    
    result = db[VideoEvidence.COLLECTION_NAME].update_one(
        {"_id": ObjectId(video_id)},
        update
    )
    return result.modified_count > 0


# =============================================================================
# Processing Services
# =============================================================================

def start_processing(video_id: str) -> Dict[str, Any]:
    """
    Start RAG pipeline processing for a video.
    
    Args:
        video_id: Video document ID
    
    Returns:
        Dict with job details
    """
    # Get video
    video = get_video(video_id)
    if not video:
        raise ValueError(f"Video not found: {video_id}")
    
    if video["status"] == VideoEvidence.STATUS_PROCESSING:
        raise ValueError("Video is already being processed")
    
    # Create processing job
    job_doc = ProcessingJob.create_document(
        video_id=video_id,
        cam_id=video["cam_id"],
        gps_lat=video["gps_lat"],
        gps_lng=video["gps_lng"]
    )
    
    db = _get_db()
    result = db[ProcessingJob.COLLECTION_NAME].insert_one(job_doc)
    job_id = str(result.inserted_id)
    
    # Update video status
    update_video_status(video_id, VideoEvidence.STATUS_PROCESSING)
    
    # TODO: In production, this would trigger a background task (Celery)
    # For now, return the job details
    
    return {
        "job_id": job_id,
        "video_id": video_id,
        "status": ProcessingJob.STATUS_QUEUED,
        "message": "Processing job queued. Use /api/evidence/jobs/{job_id} to check status."
    }


def get_processing_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get processing job status.
    
    Args:
        job_id: Job document ID
    
    Returns:
        Job document dict or None
    """
    try:
        db = _get_db()
        doc = db[ProcessingJob.COLLECTION_NAME].find_one({"_id": ObjectId(job_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    except Exception:
        return None