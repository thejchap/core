"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_segments() -> None:
    """Stub for test_get_segments (port deferred)."""

@test.skip("pending tryke port")
async def get_segments_entity_not_found() -> None:
    """Stub for test_get_segments_entity_not_found (port deferred)."""

@test.skip("pending tryke port")
async def get_segments_not_supported() -> None:
    """Stub for test_get_segments_not_supported (port deferred)."""
