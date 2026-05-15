"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def load_config_store() -> None:
    """Stub for test_load_config_store (port deferred)."""

@test.skip("snapshot test - port deferred")
async def save_config_store() -> None:
    """Stub for test_save_config_store (port deferred)."""
