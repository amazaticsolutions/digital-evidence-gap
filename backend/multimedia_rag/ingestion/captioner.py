"""
Frame captioning module using Microsoft Florence-2 vision model.

This module provides functionality to generate detailed text descriptions
of video frames using the Florence-2 large model from Microsoft. For every
frame, THREE captions are generated at different levels of detail:
  - brief:    Short high-level summary (<CAPTION> task)
  - detailed: Extended description (<DETAILED_CAPTION> task)
  - regional: Spatially-aware description (<MORE_DETAILED_CAPTION> task)

The model is loaded ONCE at module level and reused for all calls.

Functions:
    generate_caption: Generate a dict of three captions for a video frame
    generate_caption_batch: Generate caption dicts for multiple frames
    check_florence_available: Verify the model is loaded
"""

import io
import logging
import os
from datetime import datetime
from typing import Dict, List

from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM

from multimedia_rag import config

logger = logging.getLogger(__name__)


def _log(msg: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


# =============================================================================
# Module-level Florence-2 model loading (loaded once, reused for all calls)
# =============================================================================

_FLORENCE_MODEL_NAME = "microsoft/Florence-2-large"

_log(f"Loading Florence-2 model: {_FLORENCE_MODEL_NAME}...")
try:
    # Florence-2's remote modelling code does ``import flash_attn`` at module
    # level.  flash_attn is CUDA-only and not installable on CPU.  We inject a
    # tiny stub so the import succeeds; the model will fall back to SDPA or
    # eager attention automatically.
    import importlib
    import types as _t
    if importlib.util.find_spec("flash_attn") is None:
        import sys as _sys
        from importlib.machinery import ModuleSpec as _MS
        _stub = _t.ModuleType("flash_attn")
        _stub.__version__ = "0.0.0"                           # type: ignore[attr-defined]
        _stub.__path__ = []                                    # type: ignore[attr-defined]
        _stub.__spec__ = _MS("flash_attn", None)               # type: ignore[attr-defined]
        _sys.modules["flash_attn"] = _stub
        _bert_pad_mod = _t.ModuleType("flash_attn.bert_padding")
        _bert_pad_mod.__spec__ = _MS("flash_attn.bert_padding", None)
        _bert_pad_mod.index_first_axis = None                  # type: ignore[attr-defined]
        _bert_pad_mod.pad_input = None                         # type: ignore[attr-defined]
        _bert_pad_mod.unpad_input = None                       # type: ignore[attr-defined]
        _sys.modules["flash_attn.bert_padding"] = _bert_pad_mod

    _processor = AutoProcessor.from_pretrained(
        _FLORENCE_MODEL_NAME, trust_remote_code=True
    )
    _model = AutoModelForCausalLM.from_pretrained(
        _FLORENCE_MODEL_NAME,
        trust_remote_code=True,
    )
    _model.eval()
    _FLORENCE_LOADED = True
    _log("Florence-2 model loaded successfully.")
except Exception as _load_err:
    _processor = None
    _model = None
    _FLORENCE_LOADED = False
    _log(f"WARNING: Florence-2 failed to load: {_load_err}")
    _log("Captioning will use placeholder text until the model is available.")


# Florence-2 task tokens
_TASK_BRIEF = "<CAPTION>"
_TASK_DETAILED = "<DETAILED_CAPTION>"
_TASK_REGIONAL = "<MORE_DETAILED_CAPTION>"


def _run_florence_task(pil_image: Image.Image, task_token: str) -> str:
    """
    Run a single Florence-2 task on an image.

    Args:
        pil_image: A PIL Image object.
        task_token: Florence-2 task prompt token (e.g. '<CAPTION>').

    Returns:
        str: The generated text for the requested task.

    Raises:
        RuntimeError: If the Florence-2 model is not loaded.
    """
    if not _FLORENCE_LOADED or _model is None or _processor is None:
        raise RuntimeError(
            "Florence-2 model is not loaded. "
            "Ensure 'transformers', 'torch' and 'Pillow' are installed."
        )

    inputs = _processor(text=task_token, images=pil_image, return_tensors="pt")
    generated_ids = _model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=512,
        num_beams=3,
    )
    generated_text = _processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed = _processor.post_process_generation(
        generated_text, task=task_token, image_size=pil_image.size
    )
    # Florence-2 returns a dict keyed by the task token
    if isinstance(parsed, dict) and task_token in parsed:
        return str(parsed[task_token]).strip()
    return str(parsed).strip()


def generate_caption(image_bytes: bytes) -> Dict[str, str]:
    """
    Generate three captions for a video frame using Florence-2.

    Produces a brief, detailed, and regional caption for the given frame
    image. If Florence-2 is unavailable a fallback placeholder is returned.

    Args:
        image_bytes: JPEG-encoded image as bytes.

    Returns:
        Dict[str, str]: Dictionary with keys:
            - 'brief':    Short high-level caption.
            - 'detailed': Extended descriptive caption.
            - 'regional': Spatially-aware caption describing regions.

    Raises:
        ValueError: If the image bytes are empty or corrupted.

    Example:
        >>> with open('frame.jpg', 'rb') as f:
        ...     caps = generate_caption(f.read())
        >>> print(caps['brief'])
        'Man near trash can'
    """
    if not image_bytes:
        raise ValueError("Image bytes cannot be empty")

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Could not decode image bytes: {e}")

    if not _FLORENCE_LOADED:
        _log("WARNING: Florence-2 not loaded — returning placeholder captions")
        return {
            "brief": "[Florence-2 unavailable — no caption]",
            "detailed": "[Florence-2 unavailable — no caption]",
            "regional": "[Florence-2 unavailable — no caption]",
        }

    try:
        brief = _run_florence_task(pil_image, _TASK_BRIEF)
        detailed = _run_florence_task(pil_image, _TASK_DETAILED)
        regional = _run_florence_task(pil_image, _TASK_REGIONAL)

        return {
            "brief": brief if brief else "[empty]",
            "detailed": detailed if detailed else "[empty]",
            "regional": regional if regional else "[empty]",
        }
    except Exception as e:
        _log(f"ERROR during Florence-2 captioning: {e}")
        return {
            "brief": f"[Caption error: {str(e)[:80]}]",
            "detailed": f"[Caption error: {str(e)[:80]}]",
            "regional": f"[Caption error: {str(e)[:80]}]",
        }


def generate_caption_batch(
    image_bytes_list: List[bytes], batch_size: int = 5
) -> List[Dict[str, str]]:
    """
    Generate three-level captions for multiple frames with progress tracking.

    Frames are processed sequentially. A progress message is printed every
    *batch_size* frames.

    Args:
        image_bytes_list: List of JPEG-encoded images as bytes.
        batch_size: Number of frames between progress messages.

    Returns:
        List[Dict[str, str]]: List of caption dicts in the same order as
            the input images.
    """
    captions: List[Dict[str, str]] = []
    total = len(image_bytes_list)
    _log(f"Generating captions for {total} frames...")

    for i, image_bytes in enumerate(image_bytes_list):
        try:
            caption = generate_caption(image_bytes)
            captions.append(caption)
        except Exception as e:
            _log(f"  WARNING: Failed to caption frame {i}: {e}")
            captions.append({
                "brief": f"[error: {str(e)[:60]}]",
                "detailed": f"[error: {str(e)[:60]}]",
                "regional": f"[error: {str(e)[:60]}]",
            })

        if (i + 1) % batch_size == 0 or i == total - 1:
            _log(f"  Captioned {i + 1}/{total} frames")

    return captions


def check_florence_available() -> bool:
    """
    Check if the Florence-2 model is loaded and ready.

    Returns:
        bool: True if Florence-2 is available, False otherwise.
    """
    return _FLORENCE_LOADED
