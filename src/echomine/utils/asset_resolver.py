"""Resolve OpenAI asset pointers to actual files in the export bundle."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"RIFF", "audio/wav"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "audio/wav"),
]

_WEBP_SIGNATURE = b"WEBP"


class ResolvedAsset(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

    path: Path = Field(..., description="Absolute path to the resolved file on disk")
    detected_type: str = Field(..., description="MIME type detected via magic bytes")
    original_extension: str = Field(..., description="Original file extension from disk")
    file_id: str = Field(..., min_length=1, description="Extracted file ID from asset pointer")


_SIGNATURES: list[tuple[bytes, int, str]] = [
    (b"\x89PNG\r\n\x1a\n", 8, "image/png"),
    (b"\xff\xd8\xff", 3, "image/jpeg"),
    (b"GIF87a", 6, "image/gif"),
    (b"GIF89a", 6, "image/gif"),
]


def _detect_mime_type(file_path: Path) -> str:
    try:
        with open(file_path, "rb") as f:
            header = f.read(12)
    except OSError:
        return "application/octet-stream"

    for sig, length, mime in _SIGNATURES:
        if header[:length] == sig:
            return mime
    if header[:4] == b"RIFF":
        if header[8:12] == _WEBP_SIGNATURE:
            return "image/webp"
        if header[8:12] == b"WAVE":
            return "audio/wav"
    return "application/octet-stream"


def _extract_file_id(asset_pointer: str) -> str:
    return _SCHEME_RE.sub("", asset_pointer)


def resolve_asset(export_dir: Path, asset_pointer: str) -> ResolvedAsset | None:
    """Resolve an asset pointer to a file in the export directory.

    Args:
        export_dir: Directory containing export files
        asset_pointer: Asset URI (e.g., "sediment://file_abc123")

    Returns:
        ResolvedAsset with path and detected type, or None if not found
    """
    file_id = _extract_file_id(asset_pointer)
    if not file_id:
        return None

    for candidate in export_dir.iterdir():
        if candidate.is_file() and candidate.name.startswith(file_id):
            detected_type = _detect_mime_type(candidate)
            return ResolvedAsset(
                path=candidate.resolve(),
                detected_type=detected_type,
                original_extension=candidate.suffix,
                file_id=file_id,
            )

    return None
