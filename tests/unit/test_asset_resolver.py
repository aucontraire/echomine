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

    def test_webp_detected_via_riff_container(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_webp001-test")
        assert result is not None
        assert result.detected_type == "image/webp"

    def test_jpeg_detected(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_jpeg001-test")
        assert result is not None
        assert result.detected_type == "image/jpeg"

    def test_gif_detected(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_gif001-test")
        assert result is not None
        assert result.detected_type == "image/gif"

    def test_unknown_format_returns_octet_stream(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://file_unk001-test")
        assert result is not None
        assert result.detected_type == "application/octet-stream"

    def test_empty_asset_pointer_returns_none(self, fixture_dir: Path) -> None:
        result = resolve_asset(fixture_dir, "sediment://")
        assert result is None

    def test_oserror_returns_octet_stream(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        fake_file = tmp_path / "file_test001-data.bin"
        fake_file.write_bytes(b"dummy")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = resolve_asset(tmp_path, "sediment://file_test001")

        assert result is not None
        assert result.detected_type == "application/octet-stream"
