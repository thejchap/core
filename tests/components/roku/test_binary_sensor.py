"""Tests for the sensors provided by the Roku integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("indirect parametrize")
async def roku_binary_sensors() -> None:
    """Stub for test_roku_binary_sensors (port deferred)."""

@test.skip("indirect parametrize")
async def rokutv_binary_sensors() -> None:
    """Stub for test_rokutv_binary_sensors (port deferred)."""
