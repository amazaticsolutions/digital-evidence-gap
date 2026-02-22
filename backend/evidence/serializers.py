"""
Evidence serializers for video upload and management API.

This module defines request/response serializers for:
- Video file uploads (local storage)
- Google Drive link registration
- Batch uploads for multiple files
- Video listing and details
- Processing job management
"""

from rest_framework import serializers
from datetime import datetime


class FetchMediaRequestSerializer(serializers.Serializer):
    """
    Serializer for fetching media from Google Drive.
    """
    case_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Case ID to fetch media for"
    )
    media_type = serializers.ChoiceField(
        choices=['images', 'video'],
        required=True,
        help_text="Type of media to fetch"
    )


class MediaFileSerializer(serializers.Serializer):
    """
    Serializer for individual media file information.
    """
    file_id = serializers.CharField(help_text="Google Drive file ID")
    file_name = serializers.CharField(help_text="Original file name")
    file_url = serializers.URLField(help_text="Secure view/download URL")
    uploaded_at = serializers.DateTimeField(help_text="Upload timestamp")


class FetchMediaResponseSerializer(serializers.Serializer):
    """
    Serializer for media fetch response.
    """
    case_id = serializers.CharField(help_text="Case ID")
    media_type = serializers.CharField(help_text="Media type")
    files = serializers.ListField(
        child=MediaFileSerializer(),
        help_text="List of media files"
    )


class DeleteEvidenceRequestSerializer(serializers.Serializer):
    """
    Serializer for deleting evidence file.
    """
    file_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Google Drive file ID"
    )
    evidence_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Evidence record ID"
    )
    case_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Case ID for validation"
    )

    def validate(self, data):
        """
        Ensure at least one of file_id or evidence_id is provided.
        """
        if not data.get('file_id') and not data.get('evidence_id'):
            raise serializers.ValidationError(
                "Either file_id or evidence_id must be provided"
            )
        return data


class DeleteEvidenceResponseSerializer(serializers.Serializer):
    """
    Serializer for delete evidence response.
    """
    message = serializers.CharField(help_text="Success message")
    case_id = serializers.CharField(help_text="Case ID")
    deleted_file_id = serializers.CharField(help_text="Deleted file ID")


class VideoUploadSerializer(serializers.Serializer):
    """
    Serializer for local video file upload.
    
    Request fields:
        video: The video file to upload
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
        case_id: Associated case ID (required)
    """
    video = serializers.FileField(
        required=True,
        help_text="Video file to upload (mp4, avi, mov, webm, mkv)"
    )
    cam_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Camera identifier (e.g., 'cam1', 'lobby_camera')"
    )
    gps_lat = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS latitude of camera location"
    )
    gps_lng = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS longitude of camera location"
    )
    case_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Associated case ID (required)"
    )


class GDriveLinkSerializer(serializers.Serializer):
    """
    Serializer for Google Drive video link registration.
    
    Request fields:
        gdrive_url: Google Drive URL or file ID
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
        case_id: Associated case ID (required)
    """
    gdrive_url = serializers.CharField(
        required=True,
        help_text="Google Drive URL (e.g., https://drive.google.com/file/d/FILE_ID/view) or file ID"
    )
    cam_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Camera identifier"
    )
    gps_lat = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS latitude of camera location"
    )
    gps_lng = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS longitude of camera location"
    )
    case_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Associated case ID (required)"
    )


class GDriveUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading video/image files directly to Google Drive.
    
    Request fields:
        files: List of files to upload (videos or images)
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
        case_id: Associated case ID (required)
        folder_id: Google Drive folder ID (optional, uses default)
    """
    files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        min_length=1,
        help_text="List of video or image files to upload to Google Drive"
    )
    cam_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Camera identifier (e.g., 'cam1', 'lobby_camera')"
    )
    gps_lat = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS latitude of camera location"
    )
    gps_lng = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS longitude of camera location"
    )
    case_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Associated case ID (required)"
    )
    folder_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=200,
        help_text="Google Drive folder ID (optional, uses default if not provided)"
    )


class GDriveUploadResponseSerializer(serializers.Serializer):
    """
    Response serializer for Google Drive upload.
    """
    success = serializers.BooleanField()
    evidence_id = serializers.CharField()
    filename = serializers.CharField()
    file_size = serializers.IntegerField()
    media_type = serializers.CharField()
    duration = serializers.FloatField(allow_null=True)
    storage_type = serializers.CharField()
    gdrive_file_id = serializers.CharField()
    gdrive_url = serializers.CharField()
    status = serializers.CharField()


class GDriveBatchUploadResponseSerializer(serializers.Serializer):
    """
    Response serializer for batch Google Drive uploads.
    """
    batch_id = serializers.CharField()
    total_files = serializers.IntegerField()
    successful_uploads = serializers.IntegerField()
    failed_uploads = serializers.IntegerField()
    results = serializers.ListField(
        child=GDriveUploadResponseSerializer()
    )


class GDriveFileItemSerializer(serializers.Serializer):
    """
    Serializer for a single Google Drive file in batch upload.
    """
    gdrive_file_id = serializers.CharField(
        required=True,
        help_text="Google Drive file ID"
    )
    gdrive_url = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Google Drive URL (optional, will be constructed from file ID)"
    )
    filename = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Original filename (optional)"
    )
    gdrive_folder_path = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Folder path in Google Drive"
    )
    gdrive_folder_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Google Drive folder ID"
    )
    media_type = serializers.ChoiceField(
        choices=['video', 'image'],
        required=False,
        default='video',
        help_text="Type of media (video or image)"
    )
    file_size = serializers.IntegerField(
        required=False,
        default=0,
        help_text="File size in bytes"
    )
    mime_type = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="MIME type of the file"
    )


class GDriveBatchUploadSerializer(serializers.Serializer):
    """
    Serializer for batch Google Drive file registration.
    
    Request fields:
        files: List of Google Drive files to register
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
        case_id: Associated case ID (required)
    """
    files = serializers.ListField(
        child=GDriveFileItemSerializer(),
        required=True,
        min_length=1,
        help_text="List of Google Drive files to register"
    )
    cam_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Camera identifier"
    )
    gps_lat = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS latitude of camera location"
    )
    gps_lng = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS longitude of camera location"
    )
    case_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Associated case ID (required)"
    )


class BatchUploadResponseItemSerializer(serializers.Serializer):
    """
    Serializer for a single item in batch upload response.
    """
    success = serializers.BooleanField()
    evidence_id = serializers.CharField(required=False, allow_null=True)
    filename = serializers.CharField()
    gdrive_file_id = serializers.CharField()
    gdrive_url = serializers.CharField(required=False, allow_null=True)
    gdrive_folder_path = serializers.CharField(required=False, allow_null=True)
    media_type = serializers.CharField()
    file_size = serializers.IntegerField()
    error = serializers.CharField(required=False, allow_null=True)


class BatchUploadResponseSerializer(serializers.Serializer):
    """
    Serializer for batch upload response.
    """
    success = serializers.BooleanField()
    batch_id = serializers.CharField()
    total_files = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    case_id = serializers.CharField(allow_null=True)
    results = BatchUploadResponseItemSerializer(many=True)


class VideoResponseSerializer(serializers.Serializer):
    """
    Serializer for video upload response.
    """
    success = serializers.BooleanField()
    video_id = serializers.CharField()
    filename = serializers.CharField()
    file_size = serializers.IntegerField()
    duration = serializers.FloatField(allow_null=True)
    media_type = serializers.CharField(required=False, default='video')
    storage_type = serializers.CharField()
    local_path = serializers.CharField(required=False, allow_null=True)
    gdrive_file_id = serializers.CharField(required=False, allow_null=True)
    gdrive_url = serializers.CharField(required=False, allow_null=True)
    gdrive_folder_path = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField()


class MediaDetailSerializer(serializers.Serializer):
    """
    Serializer for media evidence details (video or image).
    """
    id = serializers.CharField()
    filename = serializers.CharField()
    media_type = serializers.CharField()
    mime_type = serializers.CharField(allow_null=True)
    cam_id = serializers.CharField()
    case_id = serializers.CharField(allow_null=True)
    uploaded_by_user_id = serializers.IntegerField(allow_null=True)
    upload_date = serializers.DateTimeField()
    file_size = serializers.IntegerField()
    duration = serializers.FloatField(allow_null=True)
    storage_type = serializers.CharField()
    local_path = serializers.CharField(allow_null=True)
    gdrive_file_id = serializers.CharField(allow_null=True)
    gdrive_url = serializers.CharField(allow_null=True)
    gdrive_folder_id = serializers.CharField(allow_null=True)
    gdrive_folder_path = serializers.CharField(allow_null=True)
    gps_lat = serializers.FloatField()
    gps_lng = serializers.FloatField()
    status = serializers.CharField()
    frames_processed = serializers.IntegerField()
    error_message = serializers.CharField(allow_null=True)
    batch_id = serializers.CharField(allow_null=True)


class VideoDetailSerializer(serializers.Serializer):
    """
    Serializer for video evidence details.
    """
    id = serializers.CharField()
    filename = serializers.CharField()
    media_type = serializers.CharField(required=False, default='video')
    cam_id = serializers.CharField()
    case_id = serializers.CharField(allow_null=True)
    uploaded_by_user_id = serializers.IntegerField(allow_null=True)
    upload_date = serializers.DateTimeField()
    file_size = serializers.IntegerField()
    duration = serializers.FloatField(allow_null=True)
    storage_type = serializers.CharField()
    local_path = serializers.CharField(allow_null=True)
    gdrive_file_id = serializers.CharField(allow_null=True)
    gdrive_url = serializers.CharField(allow_null=True)
    gdrive_folder_id = serializers.CharField(allow_null=True)
    gdrive_folder_path = serializers.CharField(allow_null=True)
    gps_lat = serializers.FloatField()
    gps_lng = serializers.FloatField()
    status = serializers.CharField()
    frames_processed = serializers.IntegerField()
    error_message = serializers.CharField(allow_null=True)
    batch_id = serializers.CharField(allow_null=True)


class VideoListSerializer(serializers.Serializer):
    """
    Serializer for video list response.
    """
    videos = VideoDetailSerializer(many=True)
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    skip = serializers.IntegerField()


class VideoListQuerySerializer(serializers.Serializer):
    """
    Serializer for media list query parameters.
    """
    case_id = serializers.CharField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        required=False,
        choices=['pending', 'processing', 'completed', 'failed']
    )
    media_type = serializers.ChoiceField(
        required=False,
        choices=['video', 'images'],
        help_text="Filter by media type (video or images)"
    )
    limit = serializers.IntegerField(required=False, default=50, min_value=1, max_value=100)
    skip = serializers.IntegerField(required=False, default=0, min_value=0)


class ProcessingStartSerializer(serializers.Serializer):
    """
    Serializer for starting video processing.
    """
    video_id = serializers.CharField(
        required=True,
        help_text="ID of the video to process"
    )


class ProcessingJobSerializer(serializers.Serializer):
    """
    Serializer for processing job details.
    """
    job_id = serializers.CharField()
    video_id = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField(required=False)
    started_at = serializers.DateTimeField(allow_null=True, required=False)
    completed_at = serializers.DateTimeField(allow_null=True, required=False)
    frames_total = serializers.IntegerField(required=False)
    frames_processed = serializers.IntegerField(required=False)
    error_message = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField(required=False)


# =============================================================================
# RAG (Retrieval-Augmented Generation) Serializers
# =============================================================================

class RAGIngestSerializer(serializers.Serializer):
    """
    Serializer for RAG video ingestion.
    
    Request fields:
        video_id: Video ID (optional, for reference)
        gdrive_url: Google Drive URL (required if gdrive_file_id not provided)
        gdrive_file_id: Google Drive file ID (required if gdrive_url not provided)
        cam_id: Camera identifier (default: 'unknown')
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
    """
    video_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Video ID for reference"
    )
    gdrive_url = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Google Drive URL (e.g., https://drive.google.com/file/d/FILE_ID/view)"
    )
    gdrive_file_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Google Drive file ID"
    )
    cam_id = serializers.CharField(
        required=False,
        default='unknown',
        max_length=100,
        help_text="Camera identifier"
    )
    gps_lat = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS latitude"
    )
    gps_lng = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS longitude"
    )


class RAGQuerySerializer(serializers.Serializer):
    """
    Serializer for RAG query request.
    
    Request fields:
        case_id: ID of the case (required)
        query: Natural language query (required)
        top_k: Maximum number of results to return (default: 10)
        enable_reid: Enable person re-identification (default: False)
        filters: Additional filters (optional)
            - video_id: Filter by video ID
            - cam_id: Filter by camera ID
    """
    case_id = serializers.CharField(
        required=True,
        help_text="ID of the case to query"
    )
    query = serializers.CharField(
        required=True,
        help_text="Natural language query (e.g., 'Show me all frames with a person in red')"
    )
    top_k = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=100,
        help_text="Maximum number of results to return (1-100)"
    )
    enable_reid = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Enable person re-identification across cameras"
    )
    filters = serializers.DictField(
        required=False,
        default=dict,
        help_text="Additional filters: video_id, cam_id"
    )


class RAGFrameResultSerializer(serializers.Serializer):
    """
    Serializer for individual frame result.
    """
    id = serializers.CharField(source='_id', required=False)
    video_id = serializers.CharField(required=False, allow_null=True)
    cam_id = serializers.CharField(required=False)
    timestamp = serializers.FloatField(required=False)
    score = serializers.FloatField(required=False)
    relevant = serializers.BooleanField(required=False)
    explanation = serializers.CharField(required=False, allow_null=True)
    caption = serializers.CharField(required=False, allow_null=True)
    gps_lat = serializers.FloatField(required=False, allow_null=True)
    gps_lng = serializers.FloatField(required=False, allow_null=True)
    reid_group = serializers.CharField(required=False, allow_null=True)
    gdrive_url = serializers.CharField(required=False, allow_null=True)
    confidence = serializers.FloatField(required=False, allow_null=True)


class RAGQueryResponseSerializer(serializers.Serializer):
    """
    Serializer for RAG query response.
    """
    chat_id = serializers.CharField(help_text="Chat ID where conversation is stored")
    user_message_id = serializers.CharField(help_text="ID of user's query message")
    assistant_message_id = serializers.CharField(help_text="ID of assistant's response message")
    query = serializers.CharField(help_text="Original query")
    total_searched = serializers.IntegerField(help_text="Number of frames searched")
    total_found = serializers.IntegerField(help_text="Number of relevant results found")
    summary = serializers.CharField(help_text="LLM-generated summary of findings")
    results = RAGFrameResultSerializer(many=True, help_text="Results sorted by relevance score")
    timeline = RAGFrameResultSerializer(many=True, help_text="Results sorted by timestamp")
    search_method = serializers.CharField(help_text="Search method used")
    queries_used = serializers.ListField(
        child=serializers.CharField(),
        help_text="Query variations used in search"
    )
    reid_warning = serializers.CharField(required=False, allow_null=True)


class RAGStatsResponseSerializer(serializers.Serializer):
    """
    Serializer for RAG system statistics.
    """
    total_videos = serializers.IntegerField(help_text="Total videos processed")
    total_frames = serializers.IntegerField(help_text="Total frames extracted")
    total_embeddings = serializers.IntegerField(help_text="Total embeddings created")
    vector_index_exists = serializers.BooleanField(help_text="Whether vector index exists")
    index_size_mb = serializers.FloatField(help_text="Index size in megabytes")
    last_updated = serializers.CharField(
        allow_null=True,
        help_text="Last update timestamp (ISO format)"
    )


# =============================================================================
# Case File Upload Serializers
# =============================================================================

class CaseFileUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading files to a specific case.
    
    Request fields:
        case_id: ID of the case (required)
        files: List of video/image files to upload (required)
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (optional)
        gps_lng: GPS longitude (optional)
        folder_id: Google Drive folder ID (optional)
    """
    case_id = serializers.CharField(
        required=True,
        help_text="ID of the case to upload files to"
    )
    files = serializers.ListField(
        child=serializers.FileField(),
        required=True,
        min_length=1,
        help_text="List of video or image files to upload (supports multiple files)"
    )
    cam_id = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Camera identifier (e.g., 'cam1', 'lobby_camera')"
    )
    gps_lat = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS latitude of camera location"
    )
    gps_lng = serializers.FloatField(
        required=False,
        default=0.0,
        help_text="GPS longitude of camera location"
    )
    folder_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=200,
        help_text="Google Drive folder ID (optional)"
    )


class CaseFileUploadItemSerializer(serializers.Serializer):
    """
    Serializer for individual uploaded file information.
    """
    evidence_id = serializers.CharField(help_text="Evidence ID in database")
    filename = serializers.CharField(help_text="Original filename")
    file_size = serializers.IntegerField(help_text="File size in bytes")
    media_type = serializers.CharField(help_text="Media type (video/image)")
    gdrive_file_id = serializers.CharField(help_text="Google Drive file ID")
    gdrive_url = serializers.CharField(help_text="Google Drive file URL")
    cam_id = serializers.CharField(help_text="Camera identifier")
    gps_lat = serializers.FloatField(help_text="GPS latitude")
    gps_lng = serializers.FloatField(help_text="GPS longitude")
    uploaded_at = serializers.DateTimeField(help_text="Upload timestamp")


class CaseFileUploadResponseSerializer(serializers.Serializer):
    """
    Serializer for case file upload response.
    """
    success = serializers.BooleanField(help_text="Whether upload was successful")
    case_id = serializers.CharField(help_text="Case ID")
    case_title = serializers.CharField(help_text="Case title")
    total_files = serializers.IntegerField(help_text="Total number of files uploaded")
    successful_uploads = serializers.IntegerField(help_text="Number of successful uploads")
    failed_uploads = serializers.IntegerField(help_text="Number of failed uploads")
    uploaded_files = serializers.ListField(
        child=CaseFileUploadItemSerializer(),
        help_text="List of successfully uploaded files with details"
    )
    failed_files = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of failed uploads with error details"
    )