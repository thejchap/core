"""The tests for Sense sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_power_sensors() -> None:
    """Stub for test_device_power_sensors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def device_energy_sensors() -> None:
    """Stub for test_device_energy_sensors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def voltage_sensors() -> None:
    """Stub for test_voltage_sensors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def active_power_sensors() -> None:
    """Stub for test_active_power_sensors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def trend_energy_sensors() -> None:
    """Stub for test_trend_energy_sensors (port deferred)."""
