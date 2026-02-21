"""
Ingestion package for the Multimedia RAG Engine.

This package provides the complete video ingestion pipeline, including:
- Downloading videos from Google Drive
- Extracting frames using ffmpeg and OpenCV
- Generating three-level captions using Microsoft Florence-2
- Creating three 384-dim embeddings (brief / detailed / regional)
- Storing frames in MongoDB Atlas (frame_embeddings + frame_metadata)

Main function:
    ingest_video: Complete ingestion pipeline for a single video file

Sub-modules:
    frame_extractor: Video frame extraction
    captioner: Frame captioning with Florence-2
    embedder: Text embedding with Sentence Transformers
    mongo_store: MongoDB storage operations
"""

from bson import Binary
from typing import Optional

from multimedia_rag.drive.gdrive import download_video_from_drive, delete_temp_video
from multimedia_rag.ingestion.frame_extractor import extract_frames
from multimedia_rag.ingestion.captioner import generate_caption
from multimedia_rag.ingestion.embedder import generate_embedding, generate_embeddings_for_captions
from multimedia_rag.ingestion.mongo_store import store_frame, check_frame_exists


def ingest_video(
    gdrive_url: str,
    cam_id: str,
    gps_lat: float,
    gps_lng: float,
    skip_existing: bool = True,
    max_frames: int | None = None,
) -> int:
    """
    Run the complete video ingestion pipeline.
    
    This function orchestrates the full ingestion process:
    1. Downloads the video from Google Drive to a temp directory
    2. Extracts frames at 1 frame per second
    3. For each frame:
       a. Generates three captions (brief / detailed / regional) via Florence-2
       b. Creates three 384-dim embeddings from those captions
       c. Stores frame data in MongoDB (frame_embeddings + frame_metadata)
    4. Deletes the temporary video file
    5. Returns the total number of frames processed
    
    Args:
        gdrive_url: Google Drive URL or file ID of the video to ingest.
        cam_id: Camera identifier string (e.g., "cam1", "lobby_cam").
            This is used in frame IDs and for organizing results by camera.
        gps_lat: GPS latitude coordinate of the camera location.
        gps_lng: GPS longitude coordinate of the camera location.
        skip_existing: If True, skip frames that already exist in the database.
            Set to False to force re-processing of all frames.
    
    Returns:
        int: Total number of frames successfully processed and stored.
    
    Raises:
        ValueError: If any input parameters are invalid.
        FileNotFoundError: If the video file is not found on Google Drive.
        ConnectionError: If unable to connect to required services
            (Ollama, MongoDB, Google Drive).
        RuntimeError: If processing fails at any stage.
    
    Example:
        >>> frames_count = ingest_video(
        ...     gdrive_url="https://drive.google.com/file/d/abc123/view",
        ...     cam_id="cam1",
        ...     gps_lat=40.7128,
        ...     gps_lng=-74.0060
        ... )
        >>> print(f"Processed {frames_count} frames")
        Processed 142 frames
    
    Notes:
        - The video is downloaded to /tmp/videos/ and deleted after processing
        - Frame images are stored as Binary in MongoDB, not on disk
        - Processing is sequential (one frame at a time) to avoid memory issues
        - Progress is printed to stdout during processing
    """
    # Validate inputs
    if not gdrive_url:
        raise ValueError("gdrive_url is required")
    if not cam_id:
        raise ValueError("cam_id is required")
    
    temp_video_path: Optional[str] = None
    frames_processed = 0
    
    try:
        # Step 1: Download video from Google Drive
        print(f"\n{'='*60}")
        print(f"STEP 1: Downloading video from Google Drive")
        print(f"{'='*60}")
        temp_video_path = download_video_from_drive(gdrive_url)
        
        # Step 2: Extract frames from video
        print(f"\n{'='*60}")
        print(f"STEP 2: Extracting frames from video")
        print(f"{'='*60}")
        frames = extract_frames(temp_video_path, cam_id)
        # Allow tests to limit frames for fast end-to-end checks
        if max_frames is not None:
            frames = frames[:max_frames]
        total_frames = len(frames)
        print(f"Extracted {total_frames} frames")
        
        # Step 3: Process each frame
        print(f"\n{'='*60}")
        print(f"STEP 3: Processing frames (caption → embed → store)")
        print(f"{'='*60}")
        
        for i, frame in enumerate(frames):
            frame_id = frame['frame_id']
            
            # Check if frame already exists (skip if processing was interrupted)
            if skip_existing and check_frame_exists(frame_id):
                print(f"  [{i+1}/{total_frames}] Skipping {frame_id} (already exists)")
                frames_processed += 1
                continue
            
            try:
                # Step 3a: Generate brief / detailed / regional captions via Florence-2
                print(f"  [{i+1}/{total_frames}] Captioning {frame_id}...")
                captions = generate_caption(frame['image_bytes'])

                # Step 3b: Generate three 384-dim embeddings from captions
                print(f"  [{i+1}/{total_frames}] Embedding {frame_id}...")
                embeddings = generate_embeddings_for_captions(captions)
                
                # Step 3c: Store frame in MongoDB
                print(f"  [{i+1}/{total_frames}] Storing {frame_id}...")
                frame_data = {
                    '_id': frame_id,
                    'cam_id': frame['cam_id'],
                    'timestamp': frame['timestamp'],
                    'caption_brief': captions['brief'],
                    'caption_detailed': captions['detailed'],
                    'caption_regional': captions['regional'],
                    'embedding_brief': embeddings['embedding_brief'],
                    'embedding_detailed': embeddings['embedding_detailed'],
                    'embedding_regional': embeddings['embedding_regional'],
                    'frame_image': Binary(frame['image_bytes']),
                    'gdrive_url': gdrive_url,
                    'gps_lat': gps_lat,
                    'gps_lng': gps_lng
                }
                store_frame(frame_data)
                
                frames_processed += 1
                print(f"  [{i+1}/{total_frames}] ✓ {frame_id} stored successfully")
                
            except Exception as e:
                print(f"  [{i+1}/{total_frames}] ✗ Error processing {frame_id}: {str(e)}")
                # Continue with next frame instead of failing completely
                continue
        
        # Step 4: Delete temporary video file
        print(f"\n{'='*60}")
        print(f"STEP 4: Cleaning up temporary files")
        print(f"{'='*60}")
        if temp_video_path:
            delete_temp_video(temp_video_path)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"INGESTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total frames in video: {total_frames}")
        print(f"Frames processed: {frames_processed}")
        print(f"Camera ID: {cam_id}")
        print(f"GPS: ({gps_lat}, {gps_lng})")
        print(f"Source: {gdrive_url}")
        
        return frames_processed
        
    except Exception as e:
        # Ensure temp file is deleted even on error
        if temp_video_path:
            try:
                delete_temp_video(temp_video_path)
            except Exception:
                pass  # Ignore cleanup errors
        raise
    finally:
        # Final cleanup
        pass


# Export main function and sub-modules
__all__ = [
    'ingest_video',
    'frame_extractor',
    'captioner',
    'embedder',
    'mongo_store'
]
