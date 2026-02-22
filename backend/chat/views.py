"""
Chat views for messaging API.

API Endpoints:
    GET    /api/chat/case/{case_id}/         - Get case chat details (chat, messages, evidence)
    POST   /api/chat/case/{case_id}/message/ - Send message to case chat
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import asyncio

from .serializers import (
    SendMessageSerializer,
    MessageResponseSerializer,
    CaseChatDetailSerializer,
    ChatbotRequestSerializer,
    ChatbotResponseSerializer,
)
from . import services


class CaseChatDetailView(APIView):
    """
    Get complete case details including chat, messages, and evidence files.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get case details with chat, messages, and evidence files",
        responses={
            200: CaseChatDetailSerializer,
            401: 'Not authenticated',
            404: 'Case not found',
        },
        tags=['Chat']
    )
    def get(self, request, case_id):
        """Get case chat details."""
        details, error = services.get_case_chat_details(case_id)

        if error:
            if "not found" in error.lower():
                return Response(
                    {"error": error},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Check ownership
        if details['case']['user_id'] != request.user.id:
            return Response(
                {"error": "You don't have permission to view this case"},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(details, status=status.HTTP_200_OK)


class SendMessageView(APIView):
    """
    Send a message to a case chat.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Send a message to a case chat",
        request_body=SendMessageSerializer,
        responses={
            201: MessageResponseSerializer,
            400: 'Validation error',
            401: 'Not authenticated',
            404: 'Case or chat not found',
        },
        tags=['Chat']
    )
    def post(self, request, case_id):
        """Send message to case chat."""
        serializer = SendMessageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create chat for the case
        from search import services as search_services

        # Verify case exists and user owns it
        case, case_error = search_services.get_case_by_id(case_id)
        if case_error:
            if "not found" in case_error.lower():
                return Response(
                    {"error": "Case not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": case_error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if case['user_id'] != request.user.id:
            return Response(
                {"error": "You don't have permission to send messages to this case"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get or create chat
        chat, chat_error = services.get_chat_by_case_id(case_id)
        if chat_error:
            return Response(
                {"error": chat_error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if not chat:
            # Create chat if it doesn't exist
            chat, create_error = services.create_chat(
                case_id=case_id,
                user_id=request.user.id,
                title=case.get('title', f'Case {case_id}')
            )
            if create_error:
                return Response(
                    {"error": create_error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Send message
        message, message_error = services.send_message(
            chat_id=chat['id'],
            user_id=request.user.id,
            content=serializer.validated_data['content'],
            message_type=serializer.validated_data.get('message_type', 'user')
        )

        if message_error:
            return Response(
                {"error": message_error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(message, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(APIView):
    """
    AI Chatbot endpoint for general conversations.
    """
    permission_classes = []  # No authentication required for chatbot

    @swagger_auto_schema(
        operation_description="Send a message to the AI chatbot and get a response",
        request_body=ChatbotRequestSerializer,
        responses={
            200: ChatbotResponseSerializer,
            400: 'Validation error',
            500: 'Internal server error',
        },
        tags=['Chatbot']
    )
    def post(self, request):
        """Send message to AI chatbot."""
        serializer = ChatbotRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = serializer.validated_data['user_id']
        user_message = serializer.validated_data['message']
        
        # Handle async chatbot conversation
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response_data, error = loop.run_until_complete(
                services.handle_chatbot_conversation(user_id, user_message)
            )
            
            loop.close()
            
            if error:
                return Response(
                    {"error": error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Chatbot service error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
