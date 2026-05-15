"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def switches_hub() -> None:
    """Stub for test_switches_hub (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def switches_protection_valve() -> None:
    """Stub for test_switches_protection_valve (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def switches_softener() -> None:
    """Stub for test_switches_softener (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def switches_filter() -> None:
    """Stub for test_switches_filter (port deferred)."""
