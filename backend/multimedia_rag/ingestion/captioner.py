"""
Frame captioning module using LLaVA vision model via Ollama.

This module provides functionality to generate detailed text descriptions
of video frames using the LLaVA (Large Language and Vision Assistant) model
running locally through Ollama. The captions focus on forensically relevant
details such as people, objects, actions, colors, and unusual activities.

Functions:
    generate_caption: Generate a detailed text caption for a video frame
"""

import base64
from typing import Optional

import ollama

from multimedia_rag import config


# Prompt template for surveillance frame analysis
CAPTION_PROMPT = """Describe this surveillance frame in detail.
Focus on people, objects, actions, colors, and anything unusual. Be specific.

Include in your description:
- Number of people visible and their approximate positions
- Physical descriptions (clothing, accessories, posture)
- Actions being performed
- Vehicles or objects of interest
- Environmental details (indoor/outdoor, time of day indicators)
- Any suspicious or unusual behavior
- Direction of movement if applicable

Provide a concise but thorough description."""


def generate_caption(image_bytes: bytes) -> str:
    """
    Generate a detailed text caption for a video frame using LLaVA.
    
    This function sends the frame image to the LLaVA vision model running
    on Ollama and returns a detailed description focusing on forensically
    relevant details such as people, objects, actions, and unusual activities.
    
    Args:
        image_bytes: JPEG-encoded image as bytes.
    
    Returns:
        str: Detailed text description of the frame contents.
    
    Raises:
        ConnectionError: If unable to connect to Ollama server.
        RuntimeError: If the LLaVA model fails to generate a response.
        ValueError: If the image bytes are invalid or corrupted.
    
    Example:
        >>> with open('frame.jpg', 'rb') as f:
        ...     image_bytes = f.read()
        >>> caption = generate_caption(image_bytes)
        >>> print(caption)
        'A person wearing a red jacket and blue jeans is walking 
         towards the camera. They are carrying a black backpack...'
    """
    if not image_bytes:
        raise ValueError("Image bytes cannot be empty")
    
    # Encode image bytes to base64 for Ollama API
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    try:
        # Create Ollama client with configured base URL
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        
        # Send image to LLaVA model for captioning
        response = client.generate(
            model=config.LLAVA_MODEL,
            prompt=CAPTION_PROMPT,
            images=[image_base64],
            options={
                'temperature': 0.3,  # Lower temperature for more consistent descriptions
                'num_predict': 500,  # Limit response length
            }
        )
        
        # Extract the generated caption from response
        caption = response.get('response', '').strip()
        
        if not caption:
            raise RuntimeError("LLaVA returned an empty response")
        
        return caption
        
    except ollama.ResponseError as e:
        raise RuntimeError(f"LLaVA model error: {str(e)}")
    except Exception as e:
        # Check if it's a connection error
        if "connection" in str(e).lower() or "refused" in str(e).lower():
            raise ConnectionError(
                f"Could not connect to Ollama server at {config.OLLAMA_BASE_URL}. "
                "Ensure Ollama is running with: ollama serve"
            )
        raise RuntimeError(f"Caption generation failed: {str(e)}")


def generate_caption_batch(image_bytes_list: list[bytes], batch_size: int = 5) -> list[str]:
    """
    Generate captions for multiple frames with progress tracking.
    
    This is a convenience function for processing multiple frames while
    providing progress feedback. Frames are processed sequentially as
    LLaVA processes one image at a time.
    
    Args:
        image_bytes_list: List of JPEG-encoded images as bytes.
        batch_size: Number of frames to process before printing progress.
    
    Returns:
        list[str]: List of captions in the same order as input images.
    
    Raises:
        Same exceptions as generate_caption.
    """
    captions = []
    total = len(image_bytes_list)
    
    print(f"Generating captions for {total} frames...")
    
    for i, image_bytes in enumerate(image_bytes_list):
        try:
            caption = generate_caption(image_bytes)
            captions.append(caption)
            
            # Progress update
            if (i + 1) % batch_size == 0 or i == total - 1:
                print(f"  Captioned {i + 1}/{total} frames")
                
        except Exception as e:
            print(f"  Warning: Failed to caption frame {i}: {str(e)}")
            captions.append(f"[Caption generation failed: {str(e)[:100]}]")
    
    return captions


def check_llava_available() -> bool:
    """
    Check if the LLaVA model is available on the Ollama server.
    
    Returns:
        bool: True if LLaVA is available, False otherwise.
    """
    try:
        client = ollama.Client(host=config.OLLAMA_BASE_URL)
        models = client.list()
        
        # Check if llava model exists
        model_names = [m.get('name', '').split(':')[0] for m in models.get('models', [])]
        return config.LLAVA_MODEL in model_names
        
    except Exception:
        return False
