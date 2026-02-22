"""
Chat serializers for messaging API.

This module defines request/response serializers for:
- Chat creation and management
- Message sending and retrieval
"""

from rest_framework import serializers


class CreateChatSerializer(serializers.Serializer):
    """
    Serializer for creating a new chat.
    """
    case_id = serializers.CharField(
        required=True,
        help_text="ID of the case to create chat for"
    )
    title = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Chat title"
    )


class ChatResponseSerializer(serializers.Serializer):
    """
    Serializer for chat response data.
    """
    id = serializers.CharField(help_text="Chat ID")
    case_id = serializers.CharField(help_text="Associated case ID")
    user_id = serializers.IntegerField(help_text="ID of user who owns the chat")
    title = serializers.CharField(help_text="Chat title")
    created_at = serializers.DateTimeField(help_text="Creation date and time")
    updated_at = serializers.DateTimeField(help_text="Last update date and time")


class SendMessageSerializer(serializers.Serializer):
    """
    Serializer for sending a message.
    """
    content = serializers.CharField(
        required=True,
        help_text="Message content"
    )
    message_type = serializers.ChoiceField(
        choices=['user', 'assistant', 'system'],
        default='user',
        help_text="Type of message"
    )


class MessageResponseSerializer(serializers.Serializer):
    """
    Serializer for message response data.
    """
    id = serializers.CharField(help_text="Message ID")
    chat_id = serializers.CharField(help_text="Parent chat ID")
    user_id = serializers.IntegerField(help_text="ID of user who sent the message")
    content = serializers.CharField(help_text="Message content")
    message_type = serializers.CharField(help_text="Type of message")
    created_at = serializers.DateTimeField(help_text="Creation date and time")


class ChatWithMessagesSerializer(serializers.Serializer):
    """
    Serializer for chat with all its messages.
    """
    chat = ChatResponseSerializer()
    messages = serializers.ListField(
        child=MessageResponseSerializer(),
        help_text="List of messages in the chat"
    )


class MediaItemSerializer(serializers.Serializer):
    """
    Serializer for media item in a message.
    """
    type = serializers.CharField(help_text="Media type: 'image' or 'video'")
    url = serializers.CharField(help_text="URL to the media file")
    description = serializers.CharField(help_text="Description of the media")
    filename = serializers.CharField(required=False, help_text="Original filename")
    file_size = serializers.IntegerField(required=False, help_text="File size in bytes")
    upload_date = serializers.CharField(required=False, help_text="Upload date")


class FormattedMessageSerializer(serializers.Serializer):
    """
    Serializer for frontend-compatible message format.
    """
    id = serializers.CharField(help_text="Message ID")
    role = serializers.CharField(help_text="Message role: 'user' or 'assistant'")
    content = serializers.CharField(help_text="Message content")
    timestamp = serializers.CharField(help_text="Message timestamp in ISO 8601 format")
    media = serializers.ListField(
        child=MediaItemSerializer(),
        help_text="List of media items attached to this message"
    )


class CaseChatDetailSerializer(serializers.Serializer):
    """
    Serializer for complete case details including chat and evidence.
    Frontend-compatible format with role-based messages and media attachments.
    """
    case_id = serializers.CharField(help_text="Case ID")
    case_name = serializers.CharField(help_text="Case name/title")
    case_description = serializers.CharField(help_text="Case description")
    total_evidence_files = serializers.IntegerField(help_text="Total number of evidence files")
    evidence_files = serializers.ListField(
        child=MediaItemSerializer(),
        help_text="List of all evidence files for the case"
    )
    messages = serializers.ListField(
        child=FormattedMessageSerializer(),
        help_text="List of chat messages with role and media"
    )