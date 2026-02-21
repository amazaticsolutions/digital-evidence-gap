"""
Google Drive integration module for downloading video files.

This module provides functionality to download video files from Google Drive
to a temporary local directory for processing. After ingestion is complete,
the temporary files should be deleted using the delete_temp_video function.

Functions:
    download_video_from_drive: Download a video file from Google Drive URL
    delete_temp_video: Remove a temporary video file after processing
"""

import os
import re
import io
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from multimedia_rag import config


def _extract_file_id(gdrive_url: str) -> str:
    """
    Extract the Google Drive file ID from various URL formats.
    
    Args:
        gdrive_url: Google Drive URL in any common format:
            - https://drive.google.com/file/d/FILE_ID/view
            - https://drive.google.com/open?id=FILE_ID
            - https://drive.google.com/uc?id=FILE_ID
            - Just the FILE_ID itself
    
    Returns:
        str: The extracted file ID.
    
    Raises:
        ValueError: If the URL format is not recognized.
    """
    # Pattern for /file/d/FILE_ID/ format
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', gdrive_url)
    if match:
        return match.group(1)
    
    # Pattern for ?id=FILE_ID format
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', gdrive_url)
    if match:
        return match.group(1)
    
    # If it looks like just a file ID (alphanumeric with dashes/underscores)
    if re.match(r'^[a-zA-Z0-9_-]+$', gdrive_url):
        return gdrive_url
    
    raise ValueError(
        f"Could not extract file ID from URL: {gdrive_url}. "
        "Expected format: https://drive.google.com/file/d/FILE_ID/view"
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
    credentials_path = config.GOOGLE_CREDENTIALS_PATH
    
    if not credentials_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. "
            "Please set it to the path of your service account JSON file."
        )
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Google credentials file not found at: {credentials_path}"
        )
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        raise ValueError(f"Failed to create Drive service: {str(e)}")


def download_video_from_drive(gdrive_url: str) -> str:
    """
    Download a video file from Google Drive to a local temporary directory.
    
    This function downloads the video file specified by the Google Drive URL
    to the configured temporary directory (/tmp/videos/). The file is saved
    with its original filename from Google Drive.
    
    Args:
        gdrive_url: Google Drive URL or file ID of the video to download.
    
    Returns:
        str: Absolute path to the downloaded video file in /tmp/videos/.
    
    Raises:
        ValueError: If the URL format is invalid or credentials are missing.
        FileNotFoundError: If the file is not found on Google Drive.
        HttpError: If there's an API error during download.
        IOError: If there's an error writing the file to disk.
    
    Example:
        >>> path = download_video_from_drive(
        ...     "https://drive.google.com/file/d/abc123/view"
        ... )
        >>> print(path)
        '/tmp/videos/surveillance_cam1.mp4'
    """
    # Extract file ID from URL
    file_id = _extract_file_id(gdrive_url)
    
    # Get authenticated Drive service
    service = _get_drive_service()
    
    try:
        # Get file metadata to retrieve the original filename
        file_metadata = service.files().get(
            fileId=file_id,
            fields='name,mimeType,size'
        ).execute()
        
        original_filename = file_metadata.get('name', f'{file_id}.mp4')
        file_size = file_metadata.get('size', 'unknown')
        mime_type = file_metadata.get('mimeType', 'unknown')
        
        print(f"Downloading: {original_filename}")
        print(f"  Size: {file_size} bytes")
        print(f"  Type: {mime_type}")
        
        # Ensure temp directory exists
        os.makedirs(config.TEMP_VIDEO_DIR, exist_ok=True)
        
        # Construct local file path
        local_path = os.path.join(config.TEMP_VIDEO_DIR, original_filename)
        
        # Download the file
        request = service.files().get_media(fileId=file_id)
        
        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"  Download progress: {progress}%")
        
        print(f"Download complete: {local_path}")
        return local_path
        
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(
                f"File not found on Google Drive: {file_id}. "
                "Ensure the file exists and is shared with the service account."
            )
        raise HttpError(
            f"Google Drive API error: {e.resp.status} - {str(e)}"
        )
    except IOError as e:
        raise IOError(f"Error writing video file to disk: {str(e)}")


def delete_temp_video(video_path: str) -> bool:
    """
    Delete a temporary video file after processing is complete.
    
    This function safely removes the video file from the temporary directory.
    It only deletes files within the configured TEMP_VIDEO_DIR to prevent
    accidental deletion of other files.
    
    Args:
        video_path: Absolute path to the video file to delete.
    
    Returns:
        bool: True if file was successfully deleted, False if file didn't exist.
    
    Raises:
        ValueError: If the path is outside the temp video directory.
        PermissionError: If there's insufficient permission to delete the file.
    
    Example:
        >>> delete_temp_video('/tmp/videos/surveillance_cam1.mp4')
        True
    """
    # Security check: ensure path is within temp directory
    abs_path = os.path.abspath(video_path)
    temp_dir = os.path.abspath(config.TEMP_VIDEO_DIR)
    
    if not abs_path.startswith(temp_dir):
        raise ValueError(
            f"Security error: Cannot delete file outside temp directory. "
            f"Path: {video_path}, Temp dir: {config.TEMP_VIDEO_DIR}"
        )
    
    if not os.path.exists(abs_path):
        print(f"File already deleted or doesn't exist: {video_path}")
        return False
    
    try:
        os.remove(abs_path)
        print(f"Deleted temporary video file: {video_path}")
        return True
    except PermissionError as e:
        raise PermissionError(f"Permission denied when deleting {video_path}: {e}")
    except Exception as e:
        raise IOError(f"Error deleting temporary video file: {str(e)}")
