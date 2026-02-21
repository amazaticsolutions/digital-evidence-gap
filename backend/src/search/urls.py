"""Search URLs"""
from django.urls import path
from . import views

urlpatterns = [
    # Run a forensic RAG query against the evidence database
    path('query/', views.query_view, name='search-query'),
    # Run person re-identification on frame IDs
    path('reid/', views.reid_view, name='search-reid'),
]
