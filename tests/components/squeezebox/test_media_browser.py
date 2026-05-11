"""Test the media browser interface. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.squeezebox module imports cleanly."""
    from homeassistant.components import squeezebox  # noqa: PLC0415
    expect(squeezebox).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_browse_media_root() -> None:
    """Stub for test_async_browse_media_root (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_browse_media_with_subitems() -> None:
    """Stub for test_async_browse_media_with_subitems (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_browse_media_for_apps() -> None:
    """Stub for test_async_browse_media_for_apps (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_search_media() -> None:
    """Stub for test_async_search_media (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_search_media_invalid_filter() -> None:
    """Stub for test_async_search_media_invalid_filter (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_search_media_invalid_type() -> None:
    """Stub for test_async_search_media_invalid_type (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_search_media_not_found() -> None:
    """Stub for test_async_search_media_not_found (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def generate_playlist_for_app() -> None:
    """Stub for test_generate_playlist_for_app (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_browse_tracks() -> None:
    """Stub for test_async_browse_tracks (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_browse_error() -> None:
    """Stub for test_async_browse_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_browse_item() -> None:
    """Stub for test_play_browse_item (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_browse_item_nonexistent() -> None:
    """Stub for test_play_browse_item_nonexistent (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_browse_item_bad_category() -> None:
    """Stub for test_play_browse_item_bad_category (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def synthetic_thumbnail_item_ids() -> None:
    """Stub for test_synthetic_thumbnail_item_ids (port deferred)."""
