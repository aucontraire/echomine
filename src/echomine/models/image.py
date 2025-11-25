"""Image reference model for multimodal message content."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImageRef(BaseModel):
    """Reference to an image attachment extracted from multimodal message content.

    Represents image_asset_pointer objects from OpenAI's multimodal_text content type.
    Maps sediment:// URIs to actual image files in the conversations directory.

    Example:
        >>> image = ImageRef(
        ...     asset_pointer="sediment://file_0000000078e461f590b377b1e0bb4642",
        ...     size_bytes=89512,
        ...     width=1536,
        ...     height=503
        ... )
        >>> image.asset_pointer
        'sediment://file_0000000078e461f590b377b1e0bb4642'

    Constitution Compliance:
        - FR-142: Frozen (immutable)
        - FR-146: mypy --strict compatible
        - FR-151: Type-safe with no Any in public fields
        - Principle VI: Strict typing mandatory
    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
        validate_assignment=True,
    )

    asset_pointer: str = Field(
        ...,
        min_length=1,
        description="Provider-specific image URI (e.g., 'sediment://file_xxx')",
    )
    content_type: Literal["image_asset_pointer"] = Field(
        default="image_asset_pointer",
        description="Type discriminator for image references",
    )
    size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Image file size in bytes",
    )
    width: Optional[int] = Field(
        default=None,
        ge=1,
        description="Image width in pixels",
    )
    height: Optional[int] = Field(
        default=None,
        ge=1,
        description="Image height in pixels",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific metadata (sanitized, dalle, etc.)",
    )
