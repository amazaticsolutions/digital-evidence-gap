"""
Frame extraction module for video processing.

This module provides functionality to extract frames from video files using
ffmpeg for efficient video decoding and OpenCV for frame processing. Frames
are extracted at a configurable rate (default: 1 frame per second) and
converted to JPEG bytes in memory without saving to disk.

Functions:
    extract_frames: Extract frames from a video file at a specified rate
    get_video_duration: Get the duration of a video file in seconds
"""

import subprocess
import tempfile
import os
from typing import List, Dict, Optional

import cv2
import numpy as np

from multimedia_rag import config


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video file in seconds using ffprobe.
    
    Args:
        video_path: Absolute path to the video file.
    
    Returns:
        float: Duration of the video in seconds.
    
    Raises:
        FileNotFoundError: If the video file doesn't exist.
        RuntimeError: If ffprobe fails to read the video.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        duration = float(result.stdout.strip())
        return duration
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe failed: {e.stderr}")
    except ValueError as e:
        raise RuntimeError(f"Could not parse video duration: {e}")


def extract_frames(video_path: str, cam_id: str) -> List[Dict]:
    """
    Extract frames from a video file at a rate of 1 frame per second.
    
    This function uses ffmpeg to extract frames and OpenCV to process them.
    Frames are resized to 640x480 and converted to JPEG bytes in memory.
    No frames are saved to disk during this process.
    
    Args:
        video_path: Absolute path to the video file to process.
        cam_id: Camera identifier string (e.g., "cam1") used in frame IDs.
    
    Returns:
        List[Dict]: A list of dictionaries, each containing:
            - frame_id (str): Unique identifier like "cam1_t0001"
            - cam_id (str): The camera identifier
            - timestamp (int): Second in the video when frame was captured
            - image_bytes (bytes): JPEG-encoded frame as bytes
    
    Raises:
        FileNotFoundError: If the video file doesn't exist.
        RuntimeError: If ffmpeg or OpenCV fails to process the video.
    
    Example:
        >>> frames = extract_frames('/tmp/videos/cam1.mp4', 'cam1')
        >>> print(frames[0])
        {
            'frame_id': 'cam1_t0001',
            'cam_id': 'cam1',
            'timestamp': 1,
            'image_bytes': b'...'
        }
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get video duration to estimate frame count
    duration = get_video_duration(video_path)
    total_frames = int(duration * config.FRAME_RATE)
    print(f"Video duration: {duration:.2f}s, extracting ~{total_frames} frames")
    
    frames = []
    
    # Use ffmpeg to pipe raw frames directly to stdout
    # Extract 1 frame per second (fps=1/FRAME_RATE)
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'fps={config.FRAME_RATE}',  # Extract at specified frame rate
        '-f', 'image2pipe',                  # Pipe output
        '-pix_fmt', 'bgr24',                 # OpenCV-compatible pixel format
        '-vcodec', 'rawvideo',               # Raw video output
        '-'                                   # Output to stdout
    ]
    
    try:
        # Start ffmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8  # Large buffer for video frames
        )
        
        # Get video dimensions from first frame extraction attempt
        # We need to know dimensions to read correct byte chunks
        # Use ffprobe to get dimensions
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0:s=x',
            video_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if probe_result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {probe_result.stderr}")
        
        dimensions = probe_result.stdout.strip().split('x')
        orig_width = int(dimensions[0])
        orig_height = int(dimensions[1])
        
        # Calculate bytes per frame (BGR = 3 bytes per pixel)
        bytes_per_frame = orig_width * orig_height * 3
        
        timestamp = 0
        
        while True:
            # Read one frame of raw video data
            raw_frame = process.stdout.read(bytes_per_frame)
            
            if len(raw_frame) != bytes_per_frame:
                # End of video or incomplete frame
                break
            
            # Convert raw bytes to numpy array
            frame = np.frombuffer(raw_frame, dtype=np.uint8)
            frame = frame.reshape((orig_height, orig_width, 3))
            
            # Resize frame to target dimensions
            frame_resized = cv2.resize(
                frame,
                (config.FRAME_WIDTH, config.FRAME_HEIGHT),
                interpolation=cv2.INTER_AREA
            )
            
            # Encode frame to JPEG bytes
            success, jpeg_buffer = cv2.imencode(
                '.jpg',
                frame_resized,
                [cv2.IMWRITE_JPEG_QUALITY, 85]  # 85% quality for good compression
            )
            
            if not success:
                print(f"Warning: Failed to encode frame at timestamp {timestamp}")
                timestamp += 1
                continue
            
            # Convert to bytes
            image_bytes = jpeg_buffer.tobytes()
            
            # Generate frame ID (e.g., "cam1_t0001")
            frame_id = f"{cam_id}_t{timestamp:04d}"
            
            # Create frame dict
            frame_data = {
                'frame_id': frame_id,
                'cam_id': cam_id,
                'timestamp': timestamp,
                'image_bytes': image_bytes
            }
            
            frames.append(frame_data)
            timestamp += 1
            
            # Progress indicator
            if timestamp % 10 == 0:
                print(f"  Extracted {timestamp} frames...")
        
        # Wait for ffmpeg to finish and get any error output
        process.stdout.close()
        stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
        process.wait()
        
        if process.returncode != 0 and not frames:
            raise RuntimeError(f"ffmpeg failed: {stderr_output}")
        
        print(f"Frame extraction complete: {len(frames)} frames extracted")
        return frames
        
    except Exception as e:
        # Ensure process is terminated on error
        if 'process' in locals():
            process.kill()
            process.wait()
        raise RuntimeError(f"Frame extraction failed: {str(e)}")


def frame_bytes_to_numpy(image_bytes: bytes) -> np.ndarray:
    """
    Convert JPEG bytes back to a numpy array (OpenCV BGR format).
    
    This utility function is used when frames need to be decoded for
    further processing (e.g., ReID feature extraction).
    
    Args:
        image_bytes: JPEG-encoded image as bytes.
    
    Returns:
        np.ndarray: OpenCV BGR image array.
    
    Raises:
        ValueError: If the bytes cannot be decoded as an image.
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    
    # Decode JPEG to BGR
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Could not decode image bytes")
    
    return image
