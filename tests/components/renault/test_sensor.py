"""Tests for Renault sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot; indirect parametrize")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_empty() -> None:
    """Stub for test_sensor_empty (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_errors() -> None:
    """Stub for test_sensor_errors (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_access_denied() -> None:
    """Stub for test_sensor_access_denied (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_not_supported() -> None:
    """Stub for test_sensor_not_supported (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_throttling_during_setup() -> None:
    """Stub for test_sensor_throttling_during_setup (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def sensor_throttling_after_init() -> None:
    """Stub for test_sensor_throttling_after_init (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def dynamic_scan_interval() -> None:
    """Stub for test_dynamic_scan_interval (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def dynamic_scan_interval_failed_coordinator() -> None:
    """Stub for test_dynamic_scan_interval_failed_coordinator (port deferred)."""
