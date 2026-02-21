"""
Evidence models for video evidence management.

This module defines MongoDB document schemas for video evidence,
including upload tracking, processing status, and metadata.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId


class VideoEvidence:
    """
    Model representing a video evidence file.
    
    This class defines the schema for video evidence documents stored
    in MongoDB. Videos can be stored locally or on Google Drive.
    
    Attributes:
        _id: Unique identifier for the video
        filename: Original filename of the uploaded video
        cam_id: Camera identifier for the video source
        case_id: Associated case identifier (optional)
        upload_date: Timestamp when video was uploaded
        file_size: Size of the video file in bytes
        duration: Duration of the video in seconds (optional)
        storage_type: Where the video is stored ('local' or 'gdrive')
        local_path: Path to locally stored video (if storage_type='local')
        gdrive_file_id: Google Drive file ID (if storage_type='gdrive')
        gdrive_url: Google Drive view URL (if storage_type='gdrive')
        gps_lat: GPS latitude of camera location
        gps_lng: GPS longitude of camera location
        status: Processing status ('pending', 'processing', 'completed', 'failed')
        frames_processed: Number of frames processed by RAG pipeline
        error_message: Error message if processing failed
        metadata: Additional metadata dictionary
    """
    
    COLLECTION_NAME = "video_evidence"
    
    # Status constants
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    
    # Storage type constants
    STORAGE_LOCAL = "local"
    STORAGE_GDRIVE = "gdrive"
    
    @staticmethod
    def create_document(
        filename: str,
        cam_id: str,
        file_size: int,
        storage_type: str,
        gps_lat: float = 0.0,
        gps_lng: float = 0.0,
        case_id: Optional[str] = None,
        local_path: Optional[str] = None,
        gdrive_file_id: Optional[str] = None,
        gdrive_url: Optional[str] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new video evidence document.
        
        Args:
            filename: Original filename
            cam_id: Camera identifier
            file_size: File size in bytes
            storage_type: 'local' or 'gdrive'
            gps_lat: GPS latitude
            gps_lng: GPS longitude
            case_id: Associated case ID
            local_path: Local file path
            gdrive_file_id: Google Drive file ID
            gdrive_url: Google Drive URL
            duration: Video duration in seconds
            metadata: Additional metadata
        
        Returns:
            Dict representing the document to insert
        """
        return {
            "filename": filename,
            "cam_id": cam_id,
            "case_id": case_id,
            "upload_date": datetime.utcnow(),
            "file_size": file_size,
            "duration": duration,
            "storage_type": storage_type,
            "local_path": local_path,
            "gdrive_file_id": gdrive_file_id,
            "gdrive_url": gdrive_url,
            "gps_lat": gps_lat,
            "gps_lng": gps_lng,
            "status": VideoEvidence.STATUS_PENDING,
            "frames_processed": 0,
            "error_message": None,
            "metadata": metadata or {}
        }


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