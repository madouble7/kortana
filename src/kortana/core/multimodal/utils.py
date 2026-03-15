"""
Utility functions for multimodal content handling.

This module provides helper functions for content validation, conversion,
and preparation for multimodal AI processing.
"""

import base64
import io
import logging
import mimetypes
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def encode_bytes_to_base64(data: bytes) -> str:
    """
    Encode bytes data to base64 string.

    Args:
        data: Bytes data to encode

    Returns:
        Base64-encoded string
    """
    return base64.b64encode(data).decode("utf-8")


def decode_base64_to_bytes(data: str) -> bytes:
    """
    Decode base64 string to bytes.

    Args:
        data: Base64-encoded string

    Returns:
        Decoded bytes
    """
    return base64.b64decode(data)


def is_url(data: str) -> bool:
    """
    Check if a string is a valid URL.

    Args:
        data: String to check

    Returns:
        True if the string appears to be a URL
    """
    return data.startswith(("http://", "https://", "ftp://"))


def detect_content_type(data: Union[str, bytes], filename: Optional[str] = None) -> str:
    """
    Detect the content type of data.

    Args:
        data: The data to analyze
        filename: Optional filename to help with detection

    Returns:
        Content type string (e.g., "image/png", "audio/mp3")
    """
    if filename:
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type

    # If data is a URL, try to detect from extension
    if isinstance(data, str) and is_url(data):
        content_type, _ = mimetypes.guess_type(data)
        if content_type:
            return content_type

    # Default to text if unable to detect
    return "text/plain"


def validate_audio_format(data: Union[str, bytes], allowed_formats: Optional[list] = None) -> bool:
    """
    Validate audio data format.

    Args:
        data: Audio data to validate
        allowed_formats: List of allowed formats (e.g., ["mp3", "wav", "ogg"])

    Returns:
        True if format is valid
    """
    if allowed_formats is None:
        allowed_formats = ["mp3", "wav", "ogg", "m4a", "flac", "aac"]

    content_type = detect_content_type(data)
    return any(fmt in content_type.lower() for fmt in allowed_formats)


def validate_video_format(data: Union[str, bytes], allowed_formats: Optional[list] = None) -> bool:
    """
    Validate video data format.

    Args:
        data: Video data to validate
        allowed_formats: List of allowed formats (e.g., ["mp4", "webm", "avi"])

    Returns:
        True if format is valid
    """
    if allowed_formats is None:
        allowed_formats = ["mp4", "webm", "avi", "mov", "mkv"]

    content_type = detect_content_type(data)
    return any(fmt in content_type.lower() for fmt in allowed_formats)


def validate_image_format(data: Union[str, bytes], allowed_formats: Optional[list] = None) -> bool:
    """
    Validate image data format.

    Args:
        data: Image data to validate
        allowed_formats: List of allowed formats (e.g., ["jpg", "png", "gif"])

    Returns:
        True if format is valid
    """
    if allowed_formats is None:
        allowed_formats = ["jpg", "jpeg", "png", "gif", "webp", "bmp"]

    content_type = detect_content_type(data)
    return any(fmt in content_type.lower() for fmt in allowed_formats)


def prepare_text_for_llm(text: str, max_length: Optional[int] = None) -> str:
    """
    Prepare text content for LLM processing.

    Args:
        text: Text to prepare
        max_length: Optional maximum length to truncate to

    Returns:
        Prepared text
    """
    # Remove extra whitespace
    text = " ".join(text.split())

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def prepare_image_for_llm(
    image_data: Union[str, bytes], encoding: str = "base64"
) -> Dict[str, Any]:
    """
    Prepare image data for LLM processing (e.g., GPT-4 Vision).

    Args:
        image_data: Image data (URL, base64, or bytes)
        encoding: Current encoding format

    Returns:
        Dictionary with image data ready for LLM
    """
    if isinstance(image_data, str):
        if is_url(image_data):
            return {"type": "image_url", "image_url": {"url": image_data}}
        else:
            # Assume base64
            return {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            }
    elif isinstance(image_data, bytes):
        # Convert to base64
        b64_data = encode_bytes_to_base64(image_data)
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"},
        }

    raise ValueError("Invalid image data format")


def chunk_large_content(content: str, chunk_size: int = 4000) -> list[str]:
    """
    Chunk large content into smaller pieces for processing.

    Args:
        content: Content to chunk
        chunk_size: Size of each chunk

    Returns:
        List of content chunks
    """
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    for i in range(0, len(content), chunk_size):
        chunks.append(content[i : i + chunk_size])

    return chunks


def merge_multimodal_contents(contents: list[Dict[str, Any]]) -> str:
    """
    Merge multiple content pieces into a single text representation.

    Args:
        contents: List of processed content dictionaries

    Returns:
        Merged text representation
    """
    merged_parts = []

    for content in contents:
        content_type = content.get("type")

        if content_type == "text":
            merged_parts.append(content.get("text", ""))
        elif content_type == "audio":
            if "transcription" in content:
                merged_parts.append(f"[Audio: {content['transcription']}]")
            else:
                merged_parts.append("[Audio content]")
        elif content_type == "video":
            if "description" in content:
                merged_parts.append(f"[Video: {content['description']}]")
            else:
                merged_parts.append("[Video content]")
        elif content_type == "image":
            if "caption" in content:
                merged_parts.append(f"[Image: {content['caption']}]")
            else:
                merged_parts.append("[Image content]")
        elif content_type == "simulation":
            scenario = content.get("scenario", "")
            merged_parts.append(f"[Simulation: {scenario}]")

    return "\n\n".join(merged_parts)


def extract_metadata(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from processed content.

    Args:
        content: Processed content dictionary

    Returns:
        Metadata dictionary
    """
    metadata = content.get("metadata", {})

    # Add content type info
    metadata["content_type"] = content.get("type")

    # Add format info if available
    if "format" in content:
        metadata["format"] = content["format"]

    return metadata
