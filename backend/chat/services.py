"""
Chat services for messaging functionality.

This module provides business logic for chat and message management.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from pymongo.errors import PyMongoError
from bson import ObjectId
import openai

from .models import Chat, Message


# =============================================================================
# Database Connection
# =============================================================================

def _get_db():
    """Get MongoDB database connection."""
    from pymongo import MongoClient

    # Build MongoDB URI from individual settings like in Django settings
    mongo_host = os.getenv("MONGODB_HOST", "localhost")
    mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
    db_name = os.getenv("MONGODB_DATABASE", "digital_evidence_gap")
    
    # Use MONGO_URI if provided, otherwise build from individual settings
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/{db_name}"

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


# =============================================================================
# Chatbot Service
# =============================================================================

def _get_openai_client():
    """Initialize OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return openai.OpenAI(api_key=api_key)


async def get_chatbot_response(user_message: str, conversation_history: List[Dict[str, str]] = None) -> str:
    """
    Get response from OpenAI API.
    
    Args:
        user_message: User's message
        conversation_history: List of previous messages for context
        
    Returns:
        AI response string
    """
    try:
        client = _get_openai_client()
        
        # Build messages for OpenAI API
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant for a digital evidence gap forensic video analysis system. You help users with questions about evidence management, video processing, and case analysis."
            }
        ]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": "user" if msg["message_type"] == "user" else "assistant",
                    "content": msg["content"]
                })
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        # Use ThreadPoolExecutor to run the sync OpenAI call
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
            )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I apologize, but I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"


async def handle_chatbot_conversation(
    user_id: str, 
    user_message: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Handle a complete chatbot conversation.
    
    Args:
        user_id: User ID
        user_message: User's message
        
    Returns:
        Tuple of (response_data, error_message)
    """
    try:
        db = _get_db()
        
        # Get or create user's general chatbot conversation
        chat_id = f"chatbot_{user_id}"
        
        # Get conversation history
        messages_collection = db[Message.COLLECTION_NAME]
        history = list(messages_collection.find(
            {"chat_id": chat_id}
        ).sort("created_at", -1).limit(20))
        
        # Reverse to get chronological order
        history.reverse()
        
        # Get AI response
        ai_response = await get_chatbot_response(user_message, history)
        
        # Store user message
        user_msg_doc = Message.create_document(
            chat_id=chat_id,
            user_id=int(user_id) if user_id.isdigit() else 0,
            content=user_message,
            message_type=Message.TYPE_USER
        )
        print(f"DEBUG: Storing user message: {user_msg_doc}")
        user_result = messages_collection.insert_one(user_msg_doc)
        print(f"DEBUG: User message stored with ID: {user_result.inserted_id}")
        
        # Store AI response
        ai_msg_doc = Message.create_document(
            chat_id=chat_id,
            user_id=0,  # System user
            content=ai_response,
            message_type=Message.TYPE_ASSISTANT
        )
        print(f"DEBUG: Storing AI message: {ai_msg_doc}")
        ai_result = messages_collection.insert_one(ai_msg_doc)
        print(f"DEBUG: AI message stored with ID: {ai_result.inserted_id}")
        
        # Return response data
        timestamp = datetime.utcnow()
        response_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": timestamp
        }
        
        return response_data, None
        
    except Exception as e:
        return None, f"Chatbot service error: {str(e)}"