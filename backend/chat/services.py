"""
Chat services for messaging functionality.

This module provides business logic for chat and message management.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid

from pymongo.errors import PyMongoError
from bson import ObjectId

from .models import Chat, Message


# =============================================================================
# Database Connection
# =============================================================================

def _get_db():
    """Get MongoDB database connection."""
    from pymongo import MongoClient

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "digital_evidence_gap")

    client = MongoClient(mongo_uri)
    return client[db_name]


def create_chat(
    case_id: str,
    user_id: int,
    title: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Create a new chat for a case.

    Args:
        case_id: ID of the associated case
        user_id: ID of the user
        title: Chat title
        metadata: Additional metadata

    Returns:
        Tuple of (chat_document, error_message)
    """
    try:
        db = _get_db()
        collection = db[Chat.COLLECTION_NAME]

        # Check if chat already exists for this case
        existing_chat = collection.find_one({"case_id": case_id})
        if existing_chat:
            return _format_chat_document(existing_chat), None

        # Create new chat document
        chat_doc = Chat.create_document(
            case_id=case_id,
            user_id=user_id,
            title=title,
            metadata=metadata
        )

        result = collection.insert_one(chat_doc)
        chat_doc["_id"] = result.inserted_id

        return _format_chat_document(chat_doc), None

    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def get_chat_by_case_id(case_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Get chat for a specific case.

    Args:
        case_id: Case ID

    Returns:
        Tuple of (chat_document, error_message)
    """
    try:
        db = _get_db()
        collection = db[Chat.COLLECTION_NAME]

        chat_doc = collection.find_one({"case_id": case_id})

        if not chat_doc:
            return None, None  # No chat found, but not an error

        return _format_chat_document(chat_doc), None

    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def send_message(
    chat_id: str,
    user_id: int,
    content: str,
    message_type: str = Message.TYPE_USER,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Send a message to a chat.

    Args:
        chat_id: ID of the chat
        user_id: ID of the user sending the message
        content: Message content
        message_type: Type of message
        metadata: Additional metadata

    Returns:
        Tuple of (message_document, error_message)
    """
    try:
        db = _get_db()
        chat_collection = db[Chat.COLLECTION_NAME]
        message_collection = db[Message.COLLECTION_NAME]

        # Verify chat exists
        chat = chat_collection.find_one({"_id": ObjectId(chat_id)})
        if not chat:
            return None, "Chat not found"

        # Create message document
        message_doc = Message.create_document(
            chat_id=chat_id,
            user_id=user_id,
            content=content,
            message_type=message_type,
            metadata=metadata
        )

        result = message_collection.insert_one(message_doc)
        message_doc["_id"] = result.inserted_id

        # Update chat's updated_at timestamp
        chat_collection.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"updated_at": datetime.utcnow()}}
        )

        return _format_message_document(message_doc), None

    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def get_chat_messages(chat_id: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Get all messages for a chat.

    Args:
        chat_id: ID of the chat

    Returns:
        Tuple of (messages_list, error_message)
    """
    try:
        db = _get_db()
        collection = db[Message.COLLECTION_NAME]

        cursor = collection.find(
            {"chat_id": chat_id}
        ).sort("created_at", 1)  # Sort by creation time ascending

        messages = [_format_message_document(doc) for doc in cursor]

        return messages, None

    except PyMongoError as e:
        return [], f"Database error: {str(e)}"
    except Exception as e:
        return [], str(e)


def get_case_chat_details(case_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Get complete case details including chat and evidence.

    Args:
        case_id: Case ID

    Returns:
        Tuple of (case_details, error_message)
    """
    try:
        from search import services as search_services
        from evidence import services as evidence_services

        # Get case with evidence
        case, error = search_services.get_case_with_evidence(case_id)
        if error:
            return None, error

        # Get chat for the case
        chat, chat_error = get_chat_by_case_id(case_id)

        # Get messages if chat exists
        messages = []
        if chat:
            messages, messages_error = get_chat_messages(chat["id"])
            if messages_error:
                return None, messages_error

        # Format evidence files with paths
        evidence_files = []
        if case.get("evidence"):
            for evidence in case["evidence"]:
                evidence_files.append({
                    "id": evidence.get("id"),
                    "filename": evidence.get("filename"),
                    "file_path": evidence.get("gdrive_url", evidence.get("filename", "unknown")),
                    "file_size": evidence.get("file_size"),
                    "media_type": evidence.get("media_type"),
                    "upload_date": evidence.get("upload_date")
                })

        return {
            "case": case,
            "chat": chat,
            "messages": messages,
            "evidence_files": evidence_files
        }, None

    except Exception as e:
        return None, str(e)


def _format_chat_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format a chat document for API response."""
    return {
        "id": str(doc["_id"]),
        "case_id": doc.get("case_id"),
        "user_id": doc.get("user_id"),
        "title": doc.get("title"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _format_message_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format a message document for API response."""
    return {
        "id": str(doc["_id"]),
        "chat_id": doc.get("chat_id"),
        "user_id": doc.get("user_id"),
        "content": doc.get("content"),
        "message_type": doc.get("message_type"),
        "created_at": doc.get("created_at"),
    }