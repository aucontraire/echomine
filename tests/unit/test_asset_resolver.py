"""Unit tests for asset resolver — T026.

Validates resolve_asset() for URI scheme stripping, file ID prefix matching,
magic byte sniffing, and missing file handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from echomine.utils.asset_resolver import ResolvedAsset, resolve_asset


@pytest.fixture
def fixture_dir(request: pytest.FixtureRequest) -> Path:
    test_dir = Path(request.path).parent
    return test_dir.parent / "fixtures" / "asset_resolver"


class TestResolveAsset:
    def test_sediment_scheme_resolves(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_abc123-test")
        assert result is not None
        assert isinstance(result, ResolvedAsset)
        assert result.path.exists()
        assert result.file_id == "file_abc123-test"
        assert result.detected_type == "image/png"

    def test_file_service_scheme_resolves(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "file-service://file_def456-test")
        assert result is not None
        assert result.file_id == "file_def456-test"
        assert result.detected_type == "audio/wav"

    def test_mismatched_extension_detected_via_magic_bytes(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_ghi789-test")
        assert result is not None
        assert result.original_extension == ".dat"
        assert result.detected_type == "image/png"

    def test_wav_audio_discoverable(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_def456-test")
        assert result is not None
        assert result.detected_type == "audio/wav"

    def test_missing_file_returns_none(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_nonexistent")
        assert result is None

    def test_resolved_asset_fields(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_abc123-test")
        assert result is not None
        assert isinstance(result.path, Path)
        assert isinstance(result.detected_type, str)
        assert isinstance(result.original_extension, str)
        assert isinstance(result.file_id, str)
        assert result.original_extension == ".png"

    def test_plain_file_id_without_scheme(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "file_abc123-test")
        assert result is not None
        assert result.file_id == "file_abc123-test"
