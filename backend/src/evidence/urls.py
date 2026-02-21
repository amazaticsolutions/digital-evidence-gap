"""Evidence URLs"""
from django.urls import path
from . import views

urlpatterns = [
    # Stream or proxy a video (supports Google Drive file URLs / IDs and local temp files)
    path('video-proxy/', views.video_proxy, name='video-proxy'),
    # Ingest a video from Google Drive into the evidence database
    path('ingest/', views.ingest_video_view, name='ingest-video'),
]
