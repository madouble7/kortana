"""
Core models and schemas for multimodal AI prompt generation.

This module defines the data structures for handling various types of content
including text, voice, video, and simulation-based queries.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ContentType(str, Enum):
    """Enumeration of supported content types."""

    TEXT = "text"
    VOICE = "voice"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    SIMULATION = "simulation"
    MIXED = "mixed"


class MultimodalContent(BaseModel):
    """
    Represents a single piece of multimodal content.

    Attributes:
        content_type: The type of content (text, voice, video, etc.)
        data: The actual content data (can be text, base64, URL, etc.)
        metadata: Additional metadata about the content
        timestamp: When the content was created
    """

    content_type: ContentType
    data: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    encoding: Optional[str] = None  # e.g., "base64", "utf-8", "url"

    @validator("data")
    def validate_data(cls, v, values):
        """Validate data format based on content type."""
        content_type = values.get("content_type")
        if content_type == ContentType.TEXT and not isinstance(v, str):
            raise ValueError("Text content must be a string")
        return v

    class Config:
        use_enum_values = True


class SimulationQuery(BaseModel):
    """
    Represents a simulation-based query for scenario analysis.

    Attributes:
        scenario: Description of the scenario to simulate
        parameters: Simulation parameters and constraints
        expected_outcomes: Expected outcomes or goals
        context: Additional context for the simulation
    """

    scenario: str = Field(..., description="The scenario to simulate")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Simulation parameters"
    )
    expected_outcomes: Optional[List[str]] = Field(
        default=None, description="Expected outcomes"
    )
    context: Optional[str] = Field(default=None, description="Additional context")
    duration: Optional[str] = Field(
        default=None, description="Simulation duration or timeframe"
    )


class MultimodalPrompt(BaseModel):
    """
    Represents a complete multimodal prompt with multiple content types.

    Attributes:
        prompt_id: Unique identifier for the prompt
        contents: List of multimodal content pieces
        primary_content_type: The primary type of content
        instruction: Additional instructions for processing
        context: Contextual information
    """

    prompt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contents: List[MultimodalContent] = Field(default_factory=list)
    primary_content_type: ContentType = ContentType.TEXT
    instruction: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("contents")
    def validate_contents(cls, v):
        """Ensure at least one content piece is provided."""
        if not v:
            raise ValueError("At least one content piece must be provided")
        return v

    def add_content(
        self,
        content_type: ContentType,
        data: Union[str, bytes, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        encoding: Optional[str] = None,
    ) -> None:
        """
        Add a new content piece to the prompt.

        Args:
            content_type: Type of content to add
            data: Content data
            metadata: Optional metadata
            encoding: Optional encoding information
        """
        content = MultimodalContent(
            content_type=content_type,
            data=data,
            metadata=metadata or {},
            encoding=encoding,
        )
        self.contents.append(content)

    def get_contents_by_type(self, content_type: ContentType) -> List[MultimodalContent]:
        """
        Get all content pieces of a specific type.

        Args:
            content_type: The content type to filter by

        Returns:
            List of content pieces matching the type
        """
        return [c for c in self.contents if c.content_type == content_type]

    def has_content_type(self, content_type: ContentType) -> bool:
        """
        Check if the prompt contains a specific content type.

        Args:
            content_type: The content type to check for

        Returns:
            True if the content type exists in the prompt
        """
        return any(c.content_type == content_type for c in self.contents)

    class Config:
        use_enum_values = True


class MultimodalResponse(BaseModel):
    """
    Represents a response from processing a multimodal prompt.

    Attributes:
        response_id: Unique identifier for the response
        prompt_id: ID of the original prompt
        content: The response content
        content_type: Type of response content
        processing_info: Information about processing
        metadata: Additional metadata
    """

    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt_id: str
    content: Union[str, Dict[str, Any]]
    content_type: ContentType = ContentType.TEXT
    processing_info: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True
