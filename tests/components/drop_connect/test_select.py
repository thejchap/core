"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def selects_hub() -> None:
    """Stub for test_selects_hub (port deferred)."""
