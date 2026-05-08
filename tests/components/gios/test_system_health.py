"""Tryke skip stub for test_system_health.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gios_system_health() -> None:
    """Stub for test_gios_system_health."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gios_system_health_fail() -> None:
    """Stub for test_gios_system_health_fail."""

