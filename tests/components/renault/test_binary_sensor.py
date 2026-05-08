"""Tests for Renault binary sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot; indirect parametrize")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def binary_sensor_empty() -> None:
    """Stub for test_binary_sensor_empty (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def binary_sensor_errors() -> None:
    """Stub for test_binary_sensor_errors (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def binary_sensor_access_denied() -> None:
    """Stub for test_binary_sensor_access_denied (port deferred)."""

@test.skip("syrupy snapshot; indirect parametrize")
async def binary_sensor_not_supported() -> None:
    """Stub for test_binary_sensor_not_supported (port deferred)."""
