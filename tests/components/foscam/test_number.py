"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def number_entities() -> None:
    """Stub for test_number_entities (port deferred)."""

@test.skip("snapshot test - port deferred")
async def setting_number() -> None:
    """Stub for test_setting_number (port deferred)."""
