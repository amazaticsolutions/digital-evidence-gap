"""
Evidence app URL configuration.

Endpoints:
    POST   /upload/              - Upload video file (local storage)
    POST   /gdrive/              - Register Google Drive video link
    POST   /gdrive/batch/        - Register multiple Google Drive files
    GET    /videos/              - List all videos
    GET    /videos/<video_id>/   - Get video details
    DELETE /videos/<video_id>/   - Delete video
    POST   /process/             - Start RAG pipeline processing
    GET    /jobs/<job_id>/       - Get processing job status
"""

from django.urls import path
from .views import (
    VideoUploadView,
    GDriveLinkView,
    GDriveBatchUploadView,
    VideoListView,
    VideoDetailView,
    ProcessingStartView,
    ProcessingJobView
)

app_name = 'evidence'

urlpatterns = [
    # Video upload endpoints
    path('upload/', VideoUploadView.as_view(), name='video-upload'),
    path('gdrive/', GDriveLinkView.as_view(), name='gdrive-link'),
    path('gdrive/batch/', GDriveBatchUploadView.as_view(), name='gdrive-batch'),
    
    # Video management endpoints
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('videos/<str:video_id>/', VideoDetailView.as_view(), name='video-detail'),
    
    # Processing endpoints
    path('process/', ProcessingStartView.as_view(), name='process-start'),
    path('jobs/<str:job_id>/', ProcessingJobView.as_view(), name='job-status'),
]