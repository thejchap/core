"""Tests for the SMLIGHT sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def disabled_by_default_sensors() -> None:
    """Stub for test_disabled_by_default_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def zigbee_uptime_disconnected() -> None:
    """Stub for test_zigbee_uptime_disconnected (port deferred)."""

@test.skip("syrupy snapshot")
async def zigbee2_temp_sensor() -> None:
    """Stub for test_zigbee2_temp_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def zigbee_type_sensors() -> None:
    """Stub for test_zigbee_type_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def psram_usage_sensor() -> None:
    """Stub for test_psram_usage_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def psram_usage_sensor_not_created() -> None:
    """Stub for test_psram_usage_sensor_not_created (port deferred)."""
