"""Tryke skip stub for Nexia binary sensor tests."""

from tryke import test


@test.skip("requires translation injection for entity_id slugs")
async def create_binary_sensors() -> None:
    """Stub for test_create_binary_sensors (port deferred)."""
