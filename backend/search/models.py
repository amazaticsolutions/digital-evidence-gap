"""Search models for case search management.

This module defines MongoDB document schemas for search operations,
including user queries and associated evidence.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any


class Search:
    """
    Model representing a search/case created by a user.
    
    This class defines the schema for search documents stored
    in MongoDB. A search links a user to their uploaded evidence.
    
    Attributes:
        _id: Unique identifier for the search
        user_id: ID of the user who created the search
        case_id: Associated case identifier
        title: Title/name of the search
        description: Description of what is being searched
        query_text: The search query text
        evidence_ids: List of associated video evidence IDs
        evidence_count: Number of evidence files attached
        assigned_to_user_id: ID of the user assigned to this case
        assigned_at: Timestamp when case was assigned
        status: Search status ('active', 'completed', 'archived')
        created_at: Timestamp when search was created (date + time)
        updated_at: Timestamp when search was last updated
        metadata: Additional metadata dictionary
    """
    
    COLLECTION_NAME = "searches"
    
    # Status constants
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_ARCHIVED = "archived"
    STATUS_PENDING = "pending"
    
    @staticmethod
    def create_document(
        user_id: int,
        title: str,
        case_id: Optional[str] = None,
        description: Optional[str] = None,
        query_text: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        assigned_to_user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new search document.
        
        Args:
            user_id: ID of the user creating the search
            title: Title of the search
            case_id: Associated case ID
            description: Search description
            query_text: The search query
            evidence_ids: List of associated evidence IDs
            assigned_to_user_id: ID of user assigned to this case
            metadata: Additional metadata
        
        Returns:
            Dict representing the document to insert
        """
        now = datetime.utcnow()
        evidence_list = evidence_ids or []
        return {
            "user_id": user_id,
            "case_id": case_id,
            "title": title,
            "description": description,
            "query_text": query_text,
            "evidence_ids": evidence_list,
            "evidence_count": len(evidence_list),
            "assigned_to_user_id": assigned_to_user_id,
            "assigned_at": now if assigned_to_user_id else None,
            "status": Search.STATUS_ACTIVE,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }
    
    @staticmethod
    def assign_case_update(assigned_to_user_id: int) -> Dict[str, Any]:
        """
        Create an update document to assign a case to a user.
        
        Args:
            assigned_to_user_id: ID of the user to assign the case to
        
        Returns:
            Dict representing the update operation
        """
        now = datetime.utcnow()
        return {
            "$set": {
                "assigned_to_user_id": assigned_to_user_id,
                "assigned_at": now,
                "updated_at": now
            }
        }
    
    @staticmethod
    def unassign_case_update() -> Dict[str, Any]:
        """
        Create an update document to unassign a case.
        
        Returns:
            Dict representing the update operation
        """
        return {
            "$set": {
                "assigned_to_user_id": None,
                "assigned_at": None,
                "updated_at": datetime.utcnow()
            }
        }
    
    @staticmethod
    def add_evidence_update(evidence_id: str) -> Dict[str, Any]:
        """
        Create an update document to add evidence to a search.
        
        Args:
            evidence_id: ID of the evidence to add
        
        Returns:
            Dict representing the update operation
        """
        return {
            "$addToSet": {"evidence_ids": evidence_id},
            "$inc": {"evidence_count": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    
    @staticmethod
    def remove_evidence_update(evidence_id: str) -> Dict[str, Any]:
        """
        Create an update document to remove evidence from a search.
        
        Args:
            evidence_id: ID of the evidence to remove
        
        Returns:
            Dict representing the update operation
        """
        return {
            "$pull": {"evidence_ids": evidence_id},
            "$inc": {"evidence_count": -1},
            "$set": {"updated_at": datetime.utcnow()}
        }