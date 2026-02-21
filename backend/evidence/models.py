"""
Evidence models for video evidence management.

This module defines MongoDB document schemas for video evidence,
including upload tracking, processing status, and metadata.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId


class MediaEvidence:
    """
    Model representing a media evidence file (video or image).
    
    This class defines the schema for media evidence documents stored
    in MongoDB. Files can be stored locally or on Google Drive.
    
    Attributes:
        _id: Unique identifier for the media
        filename: Original filename of the uploaded file
        media_type: Type of media ('video' or 'image')
        cam_id: Camera identifier for the source
        case_id: Associated case identifier (optional)
        uploaded_by_user_id: ID of the user who uploaded
        search_id: Associated search ID (optional)
        upload_date: Timestamp when file was uploaded
        file_size: Size of the file in bytes
        duration: Duration of the video in seconds (for videos only)
        storage_type: Where the file is stored ('local' or 'gdrive')
        local_path: Path to locally stored file (if storage_type='local')
        gdrive_file_id: Google Drive file ID (if storage_type='gdrive')
        gdrive_url: Google Drive view URL (if storage_type='gdrive')
        gdrive_folder_id: Google Drive folder ID
        gdrive_folder_path: Folder path in Google Drive
        mime_type: MIME type of the file
        gps_lat: GPS latitude of camera location
        gps_lng: GPS longitude of camera location
        status: Processing status ('pending', 'processing', 'completed', 'failed')
        frames_processed: Number of frames processed by RAG pipeline
        error_message: Error message if processing failed
        batch_id: Batch upload identifier (for grouping multiple uploads)
        metadata: Additional metadata dictionary
    """
    
    COLLECTION_NAME = "media_evidence"
    
    # Media type constants
    MEDIA_VIDEO = "video"
    MEDIA_IMAGE = "image"
    
    # Status constants
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    
    # Storage type constants
    STORAGE_LOCAL = "local"
    STORAGE_GDRIVE = "gdrive"
    
    # Allowed MIME types
    ALLOWED_VIDEO_MIMES = {
        'video/mp4', 'video/avi', 'video/mov', 'video/quicktime',
        'video/x-msvideo', 'video/webm', 'video/x-matroska'
    }
    ALLOWED_IMAGE_MIMES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'
    }
    
    @staticmethod
    def get_media_type(mime_type: str) -> str:
        """Determine media type from MIME type."""
        if mime_type in MediaEvidence.ALLOWED_VIDEO_MIMES:
            return MediaEvidence.MEDIA_VIDEO
        elif mime_type in MediaEvidence.ALLOWED_IMAGE_MIMES:
            return MediaEvidence.MEDIA_IMAGE
        return MediaEvidence.MEDIA_VIDEO  # Default to video
    
    @staticmethod
    def create_document(
        filename: str,
        cam_id: str,
        file_size: int,
        storage_type: str,
        uploaded_by_user_id: int,
        media_type: str = "video",
        mime_type: Optional[str] = None,
        gps_lat: float = 0.0,
        gps_lng: float = 0.0,
        case_id: Optional[str] = None,
        search_id: Optional[str] = None,
        local_path: Optional[str] = None,
        gdrive_file_id: Optional[str] = None,
        gdrive_url: Optional[str] = None,
        gdrive_folder_id: Optional[str] = None,
        gdrive_folder_path: Optional[str] = None,
        duration: Optional[float] = None,
        batch_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new media evidence document.
        
        Args:
            filename: Original filename
            cam_id: Camera identifier
            file_size: File size in bytes
            storage_type: 'local' or 'gdrive'
            uploaded_by_user_id: ID of the user uploading
            media_type: 'video' or 'image'
            mime_type: MIME type of the file
            gps_lat: GPS latitude
            gps_lng: GPS longitude
            case_id: Associated case ID
            search_id: Associated search ID
            local_path: Local file path
            gdrive_file_id: Google Drive file ID
            gdrive_url: Google Drive URL
            gdrive_folder_id: Google Drive folder ID
            gdrive_folder_path: Folder path in Google Drive
            duration: Video duration in seconds
            batch_id: Batch upload identifier
            metadata: Additional metadata
        
        Returns:
            Dict representing the document to insert
        """
        return {
            "filename": filename,
            "media_type": media_type,
            "mime_type": mime_type,
            "cam_id": cam_id,
            "case_id": case_id,
            "uploaded_by_user_id": uploaded_by_user_id,
            "search_id": search_id,
            "upload_date": datetime.utcnow(),
            "file_size": file_size,
            "duration": duration,
            "storage_type": storage_type,
            "local_path": local_path,
            "gdrive_file_id": gdrive_file_id,
            "gdrive_url": gdrive_url,
            "gdrive_folder_id": gdrive_folder_id,
            "gdrive_folder_path": gdrive_folder_path,
            "gps_lat": gps_lat,
            "gps_lng": gps_lng,
            "status": MediaEvidence.STATUS_PENDING,
            "frames_processed": 0,
            "error_message": None,
            "batch_id": batch_id,
            "metadata": metadata or {}
        }


# Keep VideoEvidence as an alias for backward compatibility
class VideoEvidence(MediaEvidence):
    """Alias for MediaEvidence for backward compatibility."""
    COLLECTION_NAME = "video_evidence"


class ProcessingJob:
    """
    Model representing a video processing job.
    
    Tracks the progress of RAG pipeline processing for a video.
    """
    
    COLLECTION_NAME = "processing_jobs"
    
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    
    @staticmethod
    def create_document(
        video_id: str,
        cam_id: str,
        gps_lat: float,
        gps_lng: float
    ) -> Dict[str, Any]:
        """
        Create a new processing job document.
        
        Args:
            video_id: ID of the video to process
            cam_id: Camera identifier
            gps_lat: GPS latitude
            gps_lng: GPS longitude
        
        Returns:
            Dict representing the job document
        """
        return {
            "video_id": video_id,
            "cam_id": cam_id,
            "gps_lat": gps_lat,
            "gps_lng": gps_lng,
            "status": ProcessingJob.STATUS_QUEUED,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "frames_total": 0,
            "frames_processed": 0,
            "error_message": None
        }