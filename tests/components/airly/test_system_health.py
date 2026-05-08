"""Tryke skip stub for test_system_health.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airly_system_health() -> None:
    """Stub for test_airly_system_health."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airly_system_health_fail() -> None:
    """Stub for test_airly_system_health_fail."""

