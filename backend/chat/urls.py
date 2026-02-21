"""Chat app URL configuration."""

from django.urls import path

from .views import (
    CaseChatDetailView,
    SendMessageView,
)

app_name = 'chat'

urlpatterns = [
    # Case chat endpoints
    path('case/<str:case_id>/', CaseChatDetailView.as_view(), name='case-chat-detail'),
    path('case/<str:case_id>/message/', SendMessageView.as_view(), name='send-message'),
]