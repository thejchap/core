"""Tryke skip stub for test_media_source.py."""

from tryke import test


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

