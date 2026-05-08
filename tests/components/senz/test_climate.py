"""Test Senz climate platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def climate_snapshot() -> None:
    """Stub for test_climate_snapshot (port deferred)."""

@test.skip("syrupy snapshot")
async def set_target() -> None:
    """Stub for test_set_target (port deferred)."""

@test.skip("syrupy snapshot")
async def set_target_fail() -> None:
    """Stub for test_set_target_fail (port deferred)."""

@test.skip("syrupy snapshot")
async def set_hvac_mode() -> None:
    """Stub for test_set_hvac_mode (port deferred)."""

@test.skip("syrupy snapshot")
async def set_hvac_mode_fail() -> None:
    """Stub for test_set_hvac_mode_fail (port deferred)."""
