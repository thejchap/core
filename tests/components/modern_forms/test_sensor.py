"""Tryke skip stub for Modern Forms sensor tests."""

from tryke import test


@test.skip("requires translation injection for sensor entity_id slugs")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""


@test.skip("requires translation injection for sensor entity_id slugs")
async def active_sensors() -> None:
    """Stub for test_active_sensors (port deferred)."""
