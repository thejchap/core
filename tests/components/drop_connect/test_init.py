"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def bad_json() -> None:
    """Stub for test_bad_json (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def unload() -> None:
    """Stub for test_unload (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def no_mqtt() -> None:
    """Stub for test_no_mqtt (port deferred)."""
