"""Search app URL configuration."""

from django.urls import path

from .views import (
    CaseListCreateView,
    CaseDetailView,
    CaseEvidenceView,
    CaseEvidenceDeleteView,
    CaseAssignView,
)

app_name = 'search'

urlpatterns = [
    # Case management endpoints
    path('cases/', CaseListCreateView.as_view(), name='case-list-create'),
    path('cases/<str:case_id>/', CaseDetailView.as_view(), name='case-detail'),
    path('cases/<str:case_id>/evidence/', CaseEvidenceView.as_view(), name='case-evidence'),
    path('cases/<str:case_id>/evidence/<str:evidence_id>/', CaseEvidenceDeleteView.as_view(), name='case-evidence-delete'),
    path('cases/<str:case_id>/assign/', CaseAssignView.as_view(), name='case-assign'),
]