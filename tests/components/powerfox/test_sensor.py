"""Test the sensors provided by the Powerfox integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_sensors() -> None:
    """Stub for test_all_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def update_failed() -> None:
    """Stub for test_update_failed (port deferred)."""

@test.skip("syrupy snapshot")
async def skips_gas_sensors_when_report_missing() -> None:
    """Stub for test_skips_gas_sensors_when_report_missing (port deferred)."""
