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


class CaseChatDetailSerializer(serializers.Serializer):
    """
    Serializer for complete case details including chat and evidence.
    """
    case = serializers.DictField(help_text="Case details")
    chat = ChatResponseSerializer(required=False, allow_null=True)
    messages = serializers.ListField(
        child=MessageResponseSerializer(),
        required=False,
        help_text="List of chat messages"
    )
    evidence_files = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of evidence files with paths"
    )