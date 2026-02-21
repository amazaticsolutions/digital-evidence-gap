"""Search app URL configuration."""

from django.urls import path

from .views import (
    CaseListCreateView,
    CaseSummaryView,
    CaseDetailView,
    CaseEvidenceView,
    CaseEvidenceDeleteView,
    CaseAssignView,
)

app_name = 'search'

urlpatterns = [
    # Case management endpoints
    path('cases/', CaseListCreateView.as_view(), name='case-list-create'),          # GET/POST - List/Create cases
    path('cases/summary/', CaseSummaryView.as_view(), name='case-summary'),         # GET - Simplified case list
    path('cases/<str:case_id>/', CaseDetailView.as_view(), name='case-detail'),     # GET/PATCH/DELETE - Case details
    path('cases/<str:case_id>/evidence/', CaseEvidenceView.as_view(), name='case-evidence'),  # POST - Add evidence
    path('cases/<str:case_id>/evidence/<str:evidence_id>/', CaseEvidenceDeleteView.as_view(), name='case-evidence-delete'),  # DELETE - Remove evidence
    path('cases/<str:case_id>/assign/', CaseAssignView.as_view(), name='case-assign'),  # POST - Assign case
]