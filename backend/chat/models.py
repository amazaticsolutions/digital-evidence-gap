"""
Chat models for case-related messaging system.

This module defines MongoDB document schemas for chat functionality,
including chat conversations and messages related to cases.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any


class Chat:
    """
    Model representing a chat conversation for a case.

    This class defines the schema for chat documents stored
    in MongoDB. Each case can have one chat conversation.

    Attributes:
        _id: Unique identifier for the chat
        case_id: ID of the associated case
        user_id: ID of the user who owns the chat
        title: Chat title (usually same as case title)
        created_at: Timestamp when chat was created
        updated_at: Timestamp when chat was last updated
        metadata: Additional metadata dictionary
    """

    COLLECTION_NAME = "chats"

    @staticmethod
    def create_document(
        case_id: str,
        user_id: int,
        title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat document.

        Args:
            case_id: ID of the associated case
            user_id: ID of the user
            title: Chat title
            metadata: Additional metadata

        Returns:
            Chat document dictionary
        """
        now = datetime.utcnow()
        return {
            "case_id": case_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }


class Message:
    """
    Model representing a chat message.

    This class defines the schema for message documents stored
    in MongoDB. Messages belong to a chat conversation.

    Attributes:
        _id: Unique identifier for the message
        chat_id: ID of the parent chat
        user_id: ID of the user who sent the message
        content: Message content/text
        message_type: Type of message ('user', 'assistant', 'system')
        created_at: Timestamp when message was created
        metadata: Additional metadata dictionary
    """

    COLLECTION_NAME = "messages"

    # Message types
    TYPE_USER = "user"
    TYPE_ASSISTANT = "assistant"
    TYPE_SYSTEM = "system"

    @staticmethod
    def create_document(
        chat_id: str,
        user_id: int,
        content: str,
        message_type: str = TYPE_USER,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new message document.

        Args:
            chat_id: ID of the parent chat
            user_id: ID of the user
            content: Message content
            message_type: Type of message
            metadata: Additional metadata

        Returns:
            Message document dictionary
        """
        return {
            "chat_id": chat_id,
            "user_id": user_id,
            "content": content,
            "message_type": message_type,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
