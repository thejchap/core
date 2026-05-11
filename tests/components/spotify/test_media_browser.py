"""Test the media browser interface. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def browse_media_root() -> None:
    """Stub for test_browse_media_root (port deferred)."""

@test.skip("snapshot test — out of scope")
async def browse_media_categories() -> None:
    """Stub for test_browse_media_categories (port deferred)."""

@test.skip("snapshot test — out of scope")
async def browse_media_playlists() -> None:
    """Stub for test_browse_media_playlists (port deferred)."""

@test.skip("snapshot test — out of scope")
async def browsing() -> None:
    """Stub for test_browsing (port deferred)."""

@test.skip("snapshot test — out of scope")
async def invalid_spotify_url() -> None:
    """Stub for test_invalid_spotify_url (port deferred)."""

@test.skip("snapshot test — out of scope")
async def browsing_not_loaded_entry() -> None:
    """Stub for test_browsing_not_loaded_entry (port deferred)."""
