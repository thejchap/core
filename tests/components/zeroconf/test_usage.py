"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires unported fixture (not in tryke shim)")
async def multiple_zeroconf_instances() -> None:
    """Stub for test_multiple_zeroconf_instances (port deferred)."""

@test.skip("requires unported fixture (not in tryke shim)")
async def multiple_zeroconf_instances_gives_shared() -> None:
    """Stub for test_multiple_zeroconf_instances_gives_shared (port deferred)."""
