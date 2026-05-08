"""Tryke skip-stubs for tesla_fleet/test_sensor.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def sensors() -> None:
    """Stub for test_sensors."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def sensors_restore() -> None:
    """Stub for test_sensors_restore."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def charge_energy_reset() -> None:
    """Stub for test_charge_energy_reset."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def charge_energy_restore_last_reset() -> None:
    """Stub for test_charge_energy_restore_last_reset."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_history_last_reset() -> None:
    """Stub for test_energy_history_last_reset."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def energy_history_invalid_first_period() -> None:
    """Stub for test_energy_history_invalid_first_period."""

