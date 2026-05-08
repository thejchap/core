"""Tryke skip stubs for test_media_player - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_media_previous_track_maps_errors() -> None:
    """Stub for test_async_media_previous_track_maps_errors (port deferred)."""


