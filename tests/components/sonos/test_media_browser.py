"""Tests for the Sonos Media Browser. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def build_item_response() -> None:
    """Stub for test_build_item_response (port deferred)."""

@test.skip("syrupy snapshot")
async def get_media_multisegment_album_id_uses_album_segment() -> None:
    """Stub for test_get_media_multisegment_album_id_uses_album_segment (port deferred)."""

@test.skip("syrupy snapshot")
async def get_media_multisegment_album_id_prefers_exact_item_id_match() -> None:
    """Stub for test_get_media_multisegment_album_id_prefers_exact_item_id_match (port deferred)."""

@test.skip("syrupy snapshot")
async def get_media_multisegment_album_id_falls_back_to_exact_title_match() -> None:
    """Stub for test_get_media_multisegment_album_id_falls_back_to_exact_title_match (port deferred)."""

@test.skip("syrupy snapshot")
async def browse_media_root() -> None:
    """Stub for test_browse_media_root (port deferred)."""

@test.skip("syrupy snapshot")
async def browse_media_library() -> None:
    """Stub for test_browse_media_library (port deferred)."""

@test.skip("syrupy snapshot")
async def browse_media_library_albums() -> None:
    """Stub for test_browse_media_library_albums (port deferred)."""

@test.skip("syrupy snapshot")
async def browse_media_favorites() -> None:
    """Stub for test_browse_media_favorites (port deferred)."""

@test.skip("syrupy snapshot")
async def browse_media_library_folders() -> None:
    """Stub for test_browse_media_library_folders (port deferred)."""
