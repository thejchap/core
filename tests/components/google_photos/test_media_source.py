"""Tryke skip stub for test_media_source.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_photos.media_source module imports cleanly."""
    from homeassistant.components.google_photos import media_source  # noqa: PLC0415
    expect(media_source).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_config_entries() -> None:
    """Stub for test_no_config_entries."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_read_scopes() -> None:
    """Stub for test_no_read_scopes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def browse_albums() -> None:
    """Stub for test_browse_albums."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_config_entry() -> None:
    """Stub for test_invalid_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def browse_invalid_path() -> None:
    """Stub for test_browse_invalid_path."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def missing_photo_id() -> None:
    """Stub for test_missing_photo_id."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def list_media_items_failure() -> None:
    """Stub for test_list_media_items_failure."""

