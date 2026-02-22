"""Chat app URL configuration."""

from django.urls import path

from .views import (
    CaseChatDetailView,
    SendMessageView,
    ChatbotView,
)

app_name = 'chat'

urlpatterns = [
    # General chatbot endpoint
    path('', ChatbotView.as_view(), name='chatbot'),
    
    # Case chat endpoints
    path('case/<str:case_id>/', CaseChatDetailView.as_view(), name='case-chat-detail'),
    path('case/<str:case_id>/message/', SendMessageView.as_view(), name='send-message'),
]