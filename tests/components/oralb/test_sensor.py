"""Test the OralB sensors."""

from tryke import test


@test.skip("requires entity_registry_enabled_by_default + bluetooth fixtures not in shim")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""


@test.skip("requires entity_registry_enabled_by_default + bluetooth fixtures not in shim")
async def sensors_io_series_4() -> None:
    """Stub for test_sensors_io_series_4 (port deferred)."""


@test.skip("requires bluetooth fixtures not in shim")
async def sensors_battery() -> None:
    """Stub for test_sensors_battery (port deferred)."""
