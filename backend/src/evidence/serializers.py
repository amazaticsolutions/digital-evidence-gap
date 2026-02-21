"""
Evidence serializers for video upload and management API.

This module defines request/response serializers for:
- Video file uploads (local storage)
- Google Drive link registration
- Video listing and details
- Processing job management
"""

from rest_framework import serializers


class VideoUploadSerializer(serializers.Serializer):
    """
    Serializer for local video file upload.
    
    Request fields:
        video: The video file to upload
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
        case_id: Associated case ID (optional)
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
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=100,
        help_text="Associated case ID"
    )


class GDriveLinkSerializer(serializers.Serializer):
    """
    Serializer for Google Drive video link registration.
    
    Request fields:
        gdrive_url: Google Drive URL or file ID
        cam_id: Camera identifier (required)
        gps_lat: GPS latitude (default: 0.0)
        gps_lng: GPS longitude (default: 0.0)
        case_id: Associated case ID (optional)
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
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=100,
        help_text="Associated case ID"
    )


class VideoResponseSerializer(serializers.Serializer):
    """
    Serializer for video upload response.
    """
    success = serializers.BooleanField()
    video_id = serializers.CharField()
    filename = serializers.CharField()
    file_size = serializers.IntegerField()
    duration = serializers.FloatField(allow_null=True)
    storage_type = serializers.CharField()
    local_path = serializers.CharField(required=False, allow_null=True)
    gdrive_file_id = serializers.CharField(required=False, allow_null=True)
    gdrive_url = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField()


class VideoDetailSerializer(serializers.Serializer):
    """
    Serializer for video evidence details.
    """
    _id = serializers.CharField(source='id')
    filename = serializers.CharField()
    cam_id = serializers.CharField()
    case_id = serializers.CharField(allow_null=True)
    upload_date = serializers.DateTimeField()
    file_size = serializers.IntegerField()
    duration = serializers.FloatField(allow_null=True)
    storage_type = serializers.CharField()
    local_path = serializers.CharField(allow_null=True)
    gdrive_file_id = serializers.CharField(allow_null=True)
    gdrive_url = serializers.CharField(allow_null=True)
    gps_lat = serializers.FloatField()
    gps_lng = serializers.FloatField()
    status = serializers.CharField()
    frames_processed = serializers.IntegerField()
    error_message = serializers.CharField(allow_null=True)


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
    Serializer for video list query parameters.
    """
    case_id = serializers.CharField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        required=False,
        choices=['pending', 'processing', 'completed', 'failed']
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