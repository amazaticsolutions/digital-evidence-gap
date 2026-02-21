"""
Google Drive API utilities for uploading and managing files.

This module provides functionality to upload video/image files to Google Drive
using a service account for authentication.

Functions:
    upload_file_to_drive: Upload a file to Google Drive
    create_folder: Create a folder in Google Drive
    list_files: List files in a Google Drive folder
"""

import os
import mimetypes
from typing import Optional, Dict, Any, BinaryIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from django.conf import settings


def _get_credentials_path() -> str:
    """Get the path to Google service account credentials."""
    return os.getenv(
        'GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH',
        getattr(settings, 'GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH', '')
    )


def _get_default_folder_id() -> str:
    """Get the default Google Drive folder ID for uploads."""
    return os.getenv(
        'GOOGLE_DRIVE_FOLDER_ID',
        getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', '')
    )


def _get_drive_service():
    """
    Create and return an authenticated Google Drive API service.
    
    Returns:
        Resource: Authenticated Google Drive API service object.
    
    Raises:
        FileNotFoundError: If credentials file is not found.
        ValueError: If credentials are invalid.
    """
    credentials_path = _get_credentials_path()
    
    if not credentials_path:
        raise ValueError(
            "GOOGLE_DRIVE_SERVICE_ACCOUNT_KEY_PATH environment variable is not set. "
            "Please set it to the path of your service account JSON file."
        )
    
    # Handle relative paths
    if not os.path.isabs(credentials_path):
        credentials_path = os.path.join(settings.BASE_DIR, credentials_path)
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Google credentials file not found at: {credentials_path}"
        )
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
            ]
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        raise ValueError(f"Failed to create Drive service: {str(e)}")


def upload_file_to_drive(
    file_path: str,
    filename: Optional[str] = None,
    folder_id: Optional[str] = None,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a file to Google Drive.
    
    Args:
        file_path: Path to the local file to upload.
        filename: Name to give the file in Drive (defaults to original filename).
        folder_id: Google Drive folder ID to upload to (defaults to configured folder).
        mime_type: MIME type of the file (auto-detected if not provided).
    
    Returns:
        Dict containing:
            - id: Google Drive file ID
            - name: File name
            - webViewLink: Link to view the file
            - webContentLink: Direct download link (if available)
    
    Raises:
        FileNotFoundError: If the local file doesn't exist.
        HttpError: If the upload fails.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    service = _get_drive_service()
    
    # Use default folder (Shared Drive) if not specified
    if folder_id is None:
        folder_id = _get_default_folder_id()
    
    # Use original filename if not specified
    if not filename:
        filename = os.path.basename(file_path)
    
    # Auto-detect MIME type if not specified
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
    
    # File metadata
    file_metadata = {
        'name': filename
    }
    
    # Check if folder_id is a Shared Drive ID (starts with '0A')
    # Shared Drive IDs are used as driveId, not parent folder
    is_shared_drive = folder_id and folder_id.startswith('0A')
    
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    # Create media upload
    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True
    )
    
    try:
        # Build create params
        create_params = {
            'body': file_metadata,
            'media_body': media,
            'fields': 'id,name,webViewLink,webContentLink,size,mimeType',
            'supportsAllDrives': True
        }
        
        # For Shared Drives, we need to also specify driveId
        # This is only needed for some operations, but doesn't hurt
        
        # Upload file (supportsAllDrives enables Shared Drive support)
        file = service.files().create(**create_params).execute()
        
        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'webViewLink': file.get('webViewLink'),
            'webContentLink': file.get('webContentLink'),
            'size': file.get('size'),
            'mimeType': file.get('mimeType')
        }
    except HttpError as e:
        raise Exception(f"Failed to upload file to Google Drive: {str(e)}")


def upload_file_stream_to_drive(
    file_stream: BinaryIO,
    filename: str,
    folder_id: Optional[str] = None,
    mime_type: Optional[str] = None,
    file_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Upload a file stream to Google Drive.
    
    Args:
        file_stream: File-like object to upload.
        filename: Name to give the file in Drive.
        folder_id: Google Drive folder ID to upload to.
        mime_type: MIME type of the file.
        file_size: Size of the file in bytes (optional, for progress).
    
    Returns:
        Dict containing file metadata.
    """
    service = _get_drive_service()
    
    # Use default folder if not specified
    if not folder_id:
        folder_id = _get_default_folder_id()
    
    # Auto-detect MIME type if not specified
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
    
    # File metadata
    file_metadata = {
        'name': filename
    }
    
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    # Create media upload from stream
    media = MediaIoBaseUpload(
        file_stream,
        mimetype=mime_type,
        resumable=True
    )
    
    try:
        # Upload file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink,webContentLink,size,mimeType'
        ).execute()
        
        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'webViewLink': file.get('webViewLink'),
            'webContentLink': file.get('webContentLink'),
            'size': file.get('size'),
            'mimeType': file.get('mimeType')
        }
    except HttpError as e:
        raise Exception(f"Failed to upload file to Google Drive: {str(e)}")


def create_folder(
    folder_name: str,
    parent_folder_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a folder in Google Drive.
    
    Args:
        folder_name: Name of the folder to create.
        parent_folder_id: Parent folder ID (defaults to configured folder).
    
    Returns:
        Dict containing folder metadata.
    """
    service = _get_drive_service()
    
    if not parent_folder_id:
        parent_folder_id = _get_default_folder_id()
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    try:
        folder = service.files().create(
            body=file_metadata,
            fields='id,name,webViewLink'
        ).execute()
        
        return {
            'id': folder.get('id'),
            'name': folder.get('name'),
            'webViewLink': folder.get('webViewLink')
        }
    except HttpError as e:
        raise Exception(f"Failed to create folder: {str(e)}")


def list_files(
    folder_id: Optional[str] = None,
    page_size: int = 100
) -> list:
    """
    List files in a Google Drive folder.
    
    Args:
        folder_id: Folder ID to list files from.
        page_size: Maximum number of files to return.
    
    Returns:
        List of file metadata dicts.
    """
    service = _get_drive_service()
    
    if not folder_id:
        folder_id = _get_default_folder_id()
    
    query = f"'{folder_id}' in parents and trashed=false" if folder_id else "trashed=false"
    
    try:
        results = service.files().list(
            q=query,
            pageSize=page_size,
            fields="files(id,name,webViewLink,size,mimeType,createdTime)"
        ).execute()
        
        return results.get('files', [])
    except HttpError as e:
        raise Exception(f"Failed to list files: {str(e)}")


def delete_file(file_id: str) -> bool:
    """
    Delete a file from Google Drive.
    
    Args:
        file_id: Google Drive file ID to delete.
    
    Returns:
        True if successful.
    """
    service = _get_drive_service()
    
    try:
        service.files().delete(fileId=file_id).execute()
        return True
    except HttpError as e:
        raise Exception(f"Failed to delete file: {str(e)}")