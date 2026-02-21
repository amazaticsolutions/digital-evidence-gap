"""
Evidence views for video upload and management API.

API Endpoints:
    POST   /api/evidence/upload/         - Upload video file (local storage)
    POST   /api/evidence/gdrive/         - Register Google Drive video link
    POST   /api/evidence/gdrive/batch/   - Register multiple Google Drive files
    GET    /api/evidence/videos/         - List all videos
    GET    /api/evidence/videos/{id}/    - Get video details
    DELETE /api/evidence/videos/{id}/    - Delete video
    POST   /api/evidence/process/        - Start RAG pipeline processing
    GET    /api/evidence/jobs/{id}/      - Get processing job status
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    VideoUploadSerializer,
    GDriveLinkSerializer,
    GDriveBatchUploadSerializer,
    BatchUploadResponseSerializer,
    VideoResponseSerializer,
    VideoDetailSerializer,
    VideoListSerializer,
    VideoListQuerySerializer,
    ProcessingStartSerializer,
    ProcessingJobSerializer
)
from . import services


class VideoUploadView(APIView):
    """
    Upload a video file to local storage.
    
    This endpoint accepts multipart form data with a video file and metadata.
    The video is saved locally and a database record is created.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]  # TODO: Change to IsAuthenticated
    
    @swagger_auto_schema(
        operation_description="Upload a video file for evidence analysis",
        manual_parameters=[
            openapi.Parameter(
                'video',
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Video file (mp4, avi, mov, webm, mkv)'
            ),
            openapi.Parameter(
                'cam_id',
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description='Camera identifier'
            ),
            openapi.Parameter(
                'gps_lat',
                openapi.IN_FORM,
                type=openapi.TYPE_NUMBER,
                required=False,
                description='GPS latitude'
            ),
            openapi.Parameter(
                'gps_lng',
                openapi.IN_FORM,
                type=openapi.TYPE_NUMBER,
                required=False,
                description='GPS longitude'
            ),
            openapi.Parameter(
                'case_id',
                openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=False,
                description='Associated case ID'
            ),
        ],
        responses={
            201: VideoResponseSerializer,
            400: 'Validation error',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def post(self, request):
        """Upload a video file."""
        serializer = VideoUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = services.upload_video_local(
                file=serializer.validated_data['video'],
                cam_id=serializer.validated_data['cam_id'],
                gps_lat=serializer.validated_data.get('gps_lat', 0.0),
                gps_lng=serializer.validated_data.get('gps_lng', 0.0),
                case_id=serializer.validated_data.get('case_id')
            )
            return Response(result, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Upload failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GDriveLinkView(APIView):
    """
    Register a Google Drive video link for processing.
    
    Since service accounts cannot upload to personal Drive folders,
    users can manually upload videos to Drive and register the link here.
    """
    parser_classes = [JSONParser]
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a Google Drive video link",
        request_body=GDriveLinkSerializer,
        responses={
            201: VideoResponseSerializer,
            400: 'Validation error',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def post(self, request):
        """Register a Google Drive video link."""
        serializer = GDriveLinkSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = services.upload_video_gdrive_link(
                gdrive_url=serializer.validated_data['gdrive_url'],
                cam_id=serializer.validated_data['cam_id'],
                gps_lat=serializer.validated_data.get('gps_lat', 0.0),
                gps_lng=serializer.validated_data.get('gps_lng', 0.0),
                case_id=serializer.validated_data.get('case_id')
            )
            return Response(result, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Registration failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GDriveBatchUploadView(APIView):
    """
    Register multiple Google Drive files (videos/images) for processing.
    
    This endpoint accepts a list of Google Drive file information
    and creates database records for each file with their paths.
    """
    parser_classes = [JSONParser]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Register multiple Google Drive files (videos/images)",
        request_body=GDriveBatchUploadSerializer,
        responses={
            201: BatchUploadResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def post(self, request):
        """Register multiple Google Drive files."""
        serializer = GDriveBatchUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = services.upload_gdrive_batch(
                files=serializer.validated_data['files'],
                cam_id=serializer.validated_data['cam_id'],
                uploaded_by_user_id=request.user.id,
                gps_lat=serializer.validated_data.get('gps_lat', 0.0),
                gps_lng=serializer.validated_data.get('gps_lng', 0.0),
                case_id=serializer.validated_data.get('case_id')
            )
            return Response(result, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Batch upload failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoListView(APIView):
    """
    List all video evidence with optional filters.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="List all video evidence",
        manual_parameters=[
            openapi.Parameter(
                'case_id',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='Filter by case ID'
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                enum=['pending', 'processing', 'completed', 'failed'],
                description='Filter by processing status'
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Maximum results (default: 50)'
            ),
            openapi.Parameter(
                'skip',
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='Offset for pagination'
            ),
        ],
        responses={
            200: VideoListSerializer,
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def get(self, request):
        """List videos with optional filters."""
        query_serializer = VideoListQuerySerializer(data=request.query_params)
        
        if not query_serializer.is_valid():
            return Response(
                {"error": "Invalid query parameters", "details": query_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = services.list_videos(
                case_id=query_serializer.validated_data.get('case_id'),
                status=query_serializer.validated_data.get('status'),
                limit=query_serializer.validated_data.get('limit', 50),
                skip=query_serializer.validated_data.get('skip', 0)
            )
            return Response(result)
            
        except Exception as e:
            return Response(
                {"error": "Failed to list videos", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoDetailView(APIView):
    """
    Get, update, or delete a specific video evidence.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get video evidence details",
        responses={
            200: VideoDetailSerializer,
            404: 'Video not found',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def get(self, request, video_id):
        """Get video details by ID."""
        try:
            video = services.get_video(video_id)
            
            if not video:
                return Response(
                    {"error": "Video not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(video)
            
        except Exception as e:
            return Response(
                {"error": "Failed to get video", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Delete video evidence",
        responses={
            204: 'Video deleted',
            404: 'Video not found',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def delete(self, request, video_id):
        """Delete video by ID."""
        try:
            deleted = services.delete_video(video_id)
            
            if not deleted:
                return Response(
                    {"error": "Video not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            return Response(
                {"error": "Failed to delete video", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingStartView(APIView):
    """
    Start RAG pipeline processing for a video.
    """
    parser_classes = [JSONParser]
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Start RAG pipeline processing for a video",
        request_body=ProcessingStartSerializer,
        responses={
            202: ProcessingJobSerializer,
            400: 'Validation error',
            404: 'Video not found',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def post(self, request):
        """Start video processing."""
        serializer = ProcessingStartSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = services.start_processing(
                video_id=serializer.validated_data['video_id']
            )
            return Response(result, status=status.HTTP_202_ACCEPTED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to start processing", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessingJobView(APIView):
    """
    Get processing job status.
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get processing job status",
        responses={
            200: ProcessingJobSerializer,
            404: 'Job not found',
            500: 'Server error'
        },
        tags=['Evidence']
    )
    def get(self, request, job_id):
        """Get job status by ID."""
        try:
            job = services.get_processing_job(job_id)
            
            if not job:
                return Response(
                    {"error": "Job not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(job)
            
        except Exception as e:
            return Response(
                {"error": "Failed to get job status", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )