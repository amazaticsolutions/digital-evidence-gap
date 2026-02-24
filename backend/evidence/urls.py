"""
Evidence app URL configuration.

Endpoints:
    POST   /upload/              - Upload video file (local storage)
    POST   /gdrive/              - Register Google Drive video link
    POST   /gdrive/upload/       - Upload files directly to Google Drive (supports single or multiple files)
    POST   /gdrive/batch/        - Register multiple Google Drive files
    POST   /cases/upload/        - Upload files to specific case
    GET    /videos/              - List all videos
    GET    /videos/<video_id>/   - Get video details
    DELETE /videos/<video_id>/   - Delete video
    POST   /process/             - Start RAG pipeline processing
    GET    /jobs/<job_id>/       - Get processing job status
    POST   /rag/ingest/          - Ingest video into RAG system
    POST   /rag/query/           - Query RAG system with natural language
    GET    /rag/stats/           - Get RAG system statistics
"""

from django.urls import path
from .views import (
    VideoUploadView,
    GDriveLinkView,
    GDriveUploadView,
    GDriveBatchUploadView,
    VideoListView,
    VideoDetailView,
    ProcessingStartView,
    ProcessingJobView,
    CaseFileUploadView,
    FetchMediaView,
    DeleteEvidenceView,
)
from .rag_views import (
    RAGIngestView,
    RAGQueryView,
    RAGStatsView,
)

app_name = 'evidence'

urlpatterns = [
    # Video upload endpoints
    path('upload/', VideoUploadView.as_view(), name='video-upload'),
    path('gdrive/', GDriveLinkView.as_view(), name='gdrive-link'),
    path('gdrive/upload/', GDriveUploadView.as_view(), name='gdrive-upload'),
    path('gdrive/batch/', GDriveBatchUploadView.as_view(), name='gdrive-batch'),
    
    # Case file upload endpoint
    path('cases/upload/', CaseFileUploadView.as_view(), name='case-file-upload'),
    
    # Video management endpoints
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('videos/<str:video_id>/', VideoDetailView.as_view(), name='video-detail'),
    
    # Processing endpoints
    path('process/', ProcessingStartView.as_view(), name='process-start'),
    path('jobs/<str:job_id>/', ProcessingJobView.as_view(), name='job-status'),
    
    # RAG endpoints
    path('rag/ingest/', RAGIngestView.as_view(), name='rag-ingest'),
    path('rag/query/', RAGQueryView.as_view(), name='rag-query'),
    path('rag/stats/', RAGStatsView.as_view(), name='rag-stats'),
    # New media and delete endpoints
    path('media/', FetchMediaView.as_view(), name='fetch-media'),
    path('delete/', DeleteEvidenceView.as_view(), name='delete-evidence'),
]