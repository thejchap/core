"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def state() -> None:
    """Stub for test_state (port deferred)."""

@test.skip("pending tryke port")
async def name() -> None:
    """Stub for test_name (port deferred)."""

@test.skip("pending tryke port")
async def entity_category_config_raises_error() -> None:
    """Stub for test_entity_category_config_raises_error (port deferred)."""
