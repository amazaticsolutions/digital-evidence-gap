"""
Person re-identification module using torchreid with OSNet.

This module provides cross-camera person re-identification functionality
to track the same person across different camera feeds. It uses the
pretrained osnet_x1_0 model from torchreid to extract appearance features
and groups frames containing the same person based on cosine similarity.

IMPORTANT: ReID runs ONLY on query results, not on all frames during
ingestion. This keeps ingestion fast and allows ReID to be computed
on-demand for specific search results.

Functions:
    run_reid: Run person re-identification on search result frames
"""

from typing import List, Dict, Any, Optional, Tuple
import string

import numpy as np
import cv2
import torch

from multimedia_rag.ingestion.mongo_store import (
    get_frame_embedding_doc,
    store_reid_track,
    update_frame_metadata
)
from multimedia_rag.ingestion.frame_extractor import frame_bytes_to_numpy
from multimedia_rag import config


# Module-level model loading (lazy initialization)
_reid_model = None
_reid_extractor = None


def _get_reid_model():
    """
    Get or initialize the torchreid model.
    
    Uses lazy initialization to avoid loading the model unless needed.
    
    Returns:
        tuple: (model, extractor) for ReID feature extraction.
    """
    global _reid_model, _reid_extractor
    
    if _reid_model is None:
        print(f"Loading ReID model: {config.REID_MODEL}...")
        
        try:
            import torchreid
            
            # Build the model
            _reid_model = torchreid.models.build_model(
                name=config.REID_MODEL,
                num_classes=1,  # Not used for feature extraction
                pretrained=True
            )
            
            # Set to evaluation mode
            _reid_model.eval()
            
            # Move to GPU if available
            if torch.cuda.is_available():
                _reid_model = _reid_model.cuda()
                print("  ReID model loaded on GPU")
            else:
                print("  ReID model loaded on CPU")
            
            # Create feature extractor
            _reid_extractor = torchreid.utils.FeatureExtractor(
                model_name=config.REID_MODEL,
                model_path='',  # Use pretrained weights
                device='cuda' if torch.cuda.is_available() else 'cpu'
            )
            
        except ImportError:
            raise ImportError(
                "torchreid is not installed. Install it with:\n"
                "pip install torchreid"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load ReID model: {str(e)}")
    
    return _reid_model, _reid_extractor


def _preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for ReID model.
    
    Args:
        image: BGR image as numpy array.
    
    Returns:
        Preprocessed image resized to model input size.
    """
    # torchreid expects images of size 256x128 (height x width)
    target_height = 256
    target_width = 128
    
    # Resize maintaining aspect ratio by padding
    h, w = image.shape[:2]
    
    # Resize to fit within target dimensions
    scale = min(target_width / w, target_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # Pad to target size
    pad_w = (target_width - new_w) // 2
    pad_h = (target_height - new_h) // 2
    
    padded = cv2.copyMakeBorder(
        resized,
        pad_h, target_height - new_h - pad_h,
        pad_w, target_width - new_w - pad_w,
        cv2.BORDER_CONSTANT,
        value=(128, 128, 128)  # Gray padding
    )
    
    # Convert BGR to RGB
    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    
    return rgb


def _extract_reid_features(images: List[np.ndarray]) -> np.ndarray:
    """
    Extract ReID feature vectors from a list of images.
    
    Args:
        images: List of BGR images as numpy arrays.
    
    Returns:
        np.ndarray: Feature vectors of shape (N, feature_dim).
    """
    if not images:
        return np.array([])
    
    _, extractor = _get_reid_model()
    
    # Preprocess all images
    preprocessed = [_preprocess_image(img) for img in images]
    
    # Extract features using torchreid
    features = extractor(preprocessed)
    
    # Convert to numpy array
    if isinstance(features, torch.Tensor):
        features = features.cpu().numpy()
    
    return features


def _compute_similarity_matrix(features: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity matrix between all feature vectors.
    
    Args:
        features: Feature vectors of shape (N, feature_dim).
    
    Returns:
        np.ndarray: Similarity matrix of shape (N, N).
    """
    # Normalize features
    norms = np.linalg.norm(features, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)  # Avoid division by zero
    normalized = features / norms
    
    # Compute cosine similarity
    similarity = np.dot(normalized, normalized.T)
    
    return similarity


def _group_by_similarity(
    frame_ids: List[str],
    similarity_matrix: np.ndarray,
    threshold: float
) -> Dict[str, List[int]]:
    """
    Group frames by similarity using connected components.
    
    Args:
        frame_ids: List of frame identifiers.
        similarity_matrix: Pairwise similarity matrix.
        threshold: Minimum similarity to be considered same person.
    
    Returns:
        Dict mapping person_id to list of frame indices.
    """
    n = len(frame_ids)
    if n == 0:
        return {}
    
    # Track which frames have been assigned
    assigned = [False] * n
    groups = {}
    person_count = 0
    
    for i in range(n):
        if assigned[i]:
            continue
        
        # Start a new group with this frame
        person_id = f"Person_{string.ascii_uppercase[person_count % 26]}"
        if person_count >= 26:
            person_id = f"Person_{person_count + 1}"
        
        group_indices = [i]
        assigned[i] = True
        
        # Find all similar frames
        for j in range(i + 1, n):
            if not assigned[j]:
                # Check if similar to any frame in the group
                for gi in group_indices:
                    if similarity_matrix[gi, j] >= threshold:
                        group_indices.append(j)
                        assigned[j] = True
                        break
        
        groups[person_id] = group_indices
        person_count += 1
    
    return groups


def run_reid(result_ids: List[str]) -> Dict[str, str]:
    """
    Run person re-identification on a set of frame results.
    
    This function:
    1. Fetches frame images from MongoDB for each result ID
    2. Extracts ReID features using osnet_x1_0
    3. Computes pairwise cosine similarity
    4. Groups frames with similarity > 0.7 as same person
    5. Stores tracks in reid_tracks collection
    6. Updates frame_metadata with reid_group
    
    Args:
        result_ids: List of frame IDs to process (from query results).
    
    Returns:
        Dict[str, str]: Mapping of frame_id to person_id.
            Example: {"cam1_t142": "Person_A", "cam2_t051": "Person_A", ...}
    
    Raises:
        ValueError: If result_ids is empty.
        RuntimeError: If ReID feature extraction fails.
        PyMongoError: If database operations fail.
    
    Example:
        >>> frame_ids = ["cam1_t142", "cam1_t143", "cam2_t051"]
        >>> reid_mapping = run_reid(frame_ids)
        >>> print(reid_mapping)
        {'cam1_t142': 'Person_A', 'cam1_t143': 'Person_A', 'cam2_t051': 'Person_B'}
    """
    if not result_ids:
        raise ValueError("result_ids cannot be empty")
    
    print(f"\n{'='*60}")
    print(f"RUNNING PERSON RE-IDENTIFICATION")
    print(f"{'='*60}")
    print(f"Processing {len(result_ids)} frames...")
    
    # Step 1: Fetch frame images from MongoDB
    print("Step 1: Fetching frame images...")
    frames_data = []
    valid_ids = []
    
    for frame_id in result_ids:
        doc = get_frame_embedding_doc(frame_id)
        if doc and "frame_image" in doc:
            # Get image bytes from Binary
            image_binary = doc["frame_image"]
            if hasattr(image_binary, "__bytes__"):
                image_bytes = bytes(image_binary)
            else:
                image_bytes = image_binary
            
            frames_data.append({
                "frame_id": frame_id,
                "cam_id": doc.get("cam_id", "unknown"),
                "timestamp": doc.get("timestamp", 0),
                "image_bytes": image_bytes
            })
            valid_ids.append(frame_id)
        else:
            print(f"  Warning: Frame {frame_id} not found or has no image")
    
    if not frames_data:
        print("No valid frames found for ReID")
        return {}
    
    print(f"  Found {len(frames_data)} valid frames")
    
    # Step 2: Decode images and extract features
    print("Step 2: Decoding images...")
    images = []
    for fd in frames_data:
        try:
            img = frame_bytes_to_numpy(fd["image_bytes"])
            images.append(img)
        except Exception as e:
            print(f"  Warning: Failed to decode {fd['frame_id']}: {e}")
            images.append(None)
    
    # Filter out failed images
    valid_data = []
    valid_images = []
    for i, (img, fd) in enumerate(zip(images, frames_data)):
        if img is not None:
            valid_data.append(fd)
            valid_images.append(img)
    
    if not valid_images:
        print("No valid images for ReID")
        return {}
    
    print(f"  {len(valid_images)} images decoded successfully")
    
    # Step 3: Extract ReID features
    print("Step 3: Extracting ReID features...")
    try:
        features = _extract_reid_features(valid_images)
        print(f"  Feature shape: {features.shape}")
    except Exception as e:
        raise RuntimeError(f"ReID feature extraction failed: {str(e)}")
    
    # Step 4: Compute similarity and group
    print("Step 4: Computing similarity and grouping...")
    similarity = _compute_similarity_matrix(features)
    groups = _group_by_similarity(
        [fd["frame_id"] for fd in valid_data],
        similarity,
        config.REID_SIMILARITY_THRESHOLD
    )
    
    print(f"  Found {len(groups)} distinct persons")
    
    # Step 5: Build mapping and store tracks
    print("Step 5: Storing tracks and updating metadata...")
    frame_to_person = {}
    
    for person_id, indices in groups.items():
        # Build appearances list
        appearances = []
        for idx in indices:
            fd = valid_data[idx]
            appearances.append({
                "cam": fd["cam_id"],
                "ts": fd["timestamp"],
                "frame_id": fd["frame_id"]
            })
            frame_to_person[fd["frame_id"]] = person_id
        
        # Store in reid_tracks collection
        store_reid_track(person_id, appearances)
        print(f"  {person_id}: {len(appearances)} appearances")
        
        # Update frame_metadata for each frame
        for app in appearances:
            update_frame_metadata(
                app["frame_id"],
                {"reid_group": person_id}
            )
    
    print(f"\n{'='*60}")
    print(f"REID COMPLETE")
    print(f"{'='*60}")
    print(f"Frames processed: {len(valid_data)}")
    print(f"Unique persons: {len(groups)}")
    
    return frame_to_person


def get_person_track(person_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the track for a specific person.
    
    Args:
        person_id: The person identifier (e.g., "Person_A").
    
    Returns:
        Dict containing person_id and list of appearances,
        or None if person not found.
    """
    from ingestion.mongo_store import get_collection
    
    tracks_col = get_collection(config.COLLECTION_REID_TRACKS)
    return tracks_col.find_one({"person_id": person_id})


def get_all_person_tracks() -> List[Dict[str, Any]]:
    """
    Retrieve all person tracks.
    
    Returns:
        List of all track documents.
    """
    from ingestion.mongo_store import get_reid_tracks
    return get_reid_tracks()
