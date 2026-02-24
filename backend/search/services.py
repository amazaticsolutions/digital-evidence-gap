"""
Search/Case services for case management.

This module provides business logic for:
- Creating cases
- Listing user cases
- Managing case evidence
- Case assignment
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

from .models import Search
from evidence.models import VideoEvidence


# =============================================================================
# Database Connection
# =============================================================================

def _get_db():
    """Get MongoDB database connection."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "digital_evidence_gap")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return client[db_name]


# =============================================================================
# Case Services
# =============================================================================

def create_case(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    evidence_ids: Optional[List[str]] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Create a new case.
    
    Args:
        user_id: ID of the user creating the case
        title: Case title
        description: Case description (optional)
        evidence_ids: List of evidence IDs to attach (optional)
    
    Returns:
        Tuple of (case_document, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        # Generate case ID
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        
        # Create document
        document = Search.create_document(
            user_id=user_id,
            title=title,
            case_id=case_id,
            description=description,
            evidence_ids=evidence_ids
        )
        
        # Insert into MongoDB
        result = collection.insert_one(document)
        document['_id'] = result.inserted_id
        
        return _format_case_document(document), None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def get_user_cases(
    user_id: int,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[Dict[str, Any]], int, Optional[str]]:
    """
    Get all cases for a user.
    
    Args:
        user_id: ID of the user
        status_filter: Filter by status (optional)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
    
    Returns:
        Tuple of (cases_list, total_count, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        # Build query
        query = {"user_id": user_id}
        if status_filter:
            query["status"] = status_filter
        
        # Get total count
        total = collection.count_documents(query)
        
        # Get cases with pagination
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        cases = [_format_case_document(doc) for doc in cursor]
        
        return cases, total, None
        
    except PyMongoError as e:
        return [], 0, f"Database error: {str(e)}"
    except Exception as e:
        return [], 0, str(e)


def get_case_by_id(case_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Get a case by its ID.
    
    Args:
        case_id: Case document ID (ObjectId string)
    
    Returns:
        Tuple of (case_document, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        document = collection.find_one({"_id": ObjectId(case_id)})
        
        if not document:
            return None, "Case not found"
        
        return _format_case_document(document), None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def get_case_with_evidence(case_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Get a case with its evidence details.
    
    Args:
        case_id: Case document ID (ObjectId string)
    
    Returns:
        Tuple of (case_with_evidence, error_message)
    """
    try:
        db = _get_db()
        case_collection = db[Search.COLLECTION_NAME]
        evidence_collection = db[VideoEvidence.COLLECTION_NAME]
        
        # Get case
        case_doc = case_collection.find_one({"_id": ObjectId(case_id)})
        
        if not case_doc:
            return None, "Case not found"
        
        print(f"DEBUG get_case_with_evidence: Raw case_doc user_id = {case_doc.get('user_id')}, type = {type(case_doc.get('user_id'))}")
        
        case = _format_case_document(case_doc)
        
        # Get evidence details by case_id (more reliable than evidence_ids array)
        evidence_docs = list(evidence_collection.find({"case_id": case_id}))
        case["evidence"] = [_format_evidence_document(doc) for doc in evidence_docs]
        
        return case, None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def update_case(
    case_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Update a case.
    
    Args:
        case_id: Case document ID
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
    
    Returns:
        Tuple of (updated_case, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        # Build update
        update_fields = {"updated_at": datetime.utcnow()}
        if title is not None:
            update_fields["title"] = title
        if description is not None:
            update_fields["description"] = description
        if status is not None:
            update_fields["status"] = status
        
        result = collection.find_one_and_update(
            {"_id": ObjectId(case_id)},
            {"$set": update_fields},
            return_document=True
        )
        
        if not result:
            return None, "Case not found"
        
        return _format_case_document(result), None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def add_evidence_to_case(
    case_id: str,
    evidence_id: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Add evidence to a case.
    
    Args:
        case_id: Case document ID
        evidence_id: Evidence document ID
    
    Returns:
        Tuple of (updated_case, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        update = Search.add_evidence_update(evidence_id)
        
        result = collection.find_one_and_update(
            {"_id": ObjectId(case_id)},
            update,
            return_document=True
        )
        
        if not result:
            return None, "Case not found"
        
        return _format_case_document(result), None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def remove_evidence_from_case(
    case_id: str,
    evidence_id: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Remove evidence from a case.
    
    Args:
        case_id: Case document ID
        evidence_id: Evidence document ID
    
    Returns:
        Tuple of (updated_case, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        update = Search.remove_evidence_update(evidence_id)
        
        result = collection.find_one_and_update(
            {"_id": ObjectId(case_id)},
            update,
            return_document=True
        )
        
        if not result:
            return None, "Case not found"
        
        return _format_case_document(result), None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def assign_case_to_user(
    case_id: str,
    assigned_to_user_id: int
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Assign a case to a user.
    
    Args:
        case_id: Case document ID
        assigned_to_user_id: User ID to assign
    
    Returns:
        Tuple of (updated_case, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        update = Search.assign_case_update(assigned_to_user_id)
        
        result = collection.find_one_and_update(
            {"_id": ObjectId(case_id)},
            update,
            return_document=True
        )
        
        if not result:
            return None, "Case not found"
        
        return _format_case_document(result), None
        
    except PyMongoError as e:
        return None, f"Database error: {str(e)}"
    except Exception as e:
        return None, str(e)


def delete_case(case_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete a case.
    
    Args:
        case_id: Case document ID
    
    Returns:
        Tuple of (success, error_message)
    """
    try:
        db = _get_db()
        collection = db[Search.COLLECTION_NAME]
        
        result = collection.delete_one({"_id": ObjectId(case_id)})
        
        if result.deleted_count == 0:
            return False, "Case not found"
        
        return True, None
        
    except PyMongoError as e:
        return False, f"Database error: {str(e)}"
    except Exception as e:
        return False, str(e)


# =============================================================================
# Helper Functions
# =============================================================================

def _format_case_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format a case document for API response."""
    # Convert ObjectId fields to appropriate types
    case_id = doc.get("case_id")
    if isinstance(case_id, ObjectId):
        case_id = str(case_id)
    
    # user_id - convert ObjectId to string for consistent handling
    user_id = doc.get("user_id")
    print(f"DEBUG _format_case_document: Raw user_id = {user_id}, type = {type(user_id)}")
    if isinstance(user_id, ObjectId):
        user_id = str(user_id)  # Convert ObjectId to string
        print(f"DEBUG: user_id was ObjectId, converted to string: {user_id}")
    elif user_id is None:
        print(f"WARNING: user_id is None")
        user_id = None
    else:
        # Keep as-is (could be int or string)
        user_id = str(user_id)  # Convert to string for consistency
    print(f"DEBUG _format_case_document: Formatted user_id = {user_id}, type = {type(user_id)}")
    
    # assigned_to_user_id - convert ObjectId to string for consistent handling
    assigned_to = doc.get("assigned_to_user_id")
    if isinstance(assigned_to, ObjectId):
        assigned_to = str(assigned_to)  # Convert ObjectId to string
    elif assigned_to is not None:
        assigned_to = str(assigned_to)  # Convert to string for consistency
    else:
        assigned_to = None
    
    # evidence_ids should be strings
    evidence_ids = doc.get("evidence_ids", [])
    formatted_evidence_ids = []
    for eid in evidence_ids:
        if isinstance(eid, ObjectId):
            formatted_evidence_ids.append(str(eid))
        else:
            formatted_evidence_ids.append(str(eid))
    
    return {
        "id": str(doc["_id"]),
        "case_id": case_id,
        "title": doc.get("title"),
        "description": doc.get("description"),
        "user_id": user_id,
        "assigned_to_user_id": assigned_to,
        "assigned_at": doc.get("assigned_at"),
        "evidence_count": int(doc.get("evidence_count", len(doc.get("evidence_ids", [])))),
        "evidence_ids": formatted_evidence_ids,
        "status": doc.get("status"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _format_evidence_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Format an evidence document for API response."""
    return {
        "id": str(doc["_id"]),
        "filename": doc.get("filename"),
        "cam_id": doc.get("cam_id"),
        "file_size": doc.get("file_size"),
        "duration": doc.get("duration"),
        "storage_type": doc.get("storage_type"),
        "gdrive_url": doc.get("gdrive_url"),
        "gdrive_folder_path": doc.get("gdrive_folder_path"),
        "status": doc.get("status"),
        "upload_date": doc.get("upload_date"),
    }