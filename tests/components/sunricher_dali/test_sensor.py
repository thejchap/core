"""Test the Sunricher DALI sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def illuminance_callback() -> None:
    """Stub for test_illuminance_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def sensor_on_off() -> None:
    """Stub for test_sensor_on_off (port deferred)."""

@test.skip("syrupy snapshot")
async def availability() -> None:
    """Stub for test_availability (port deferred)."""

@test.skip("syrupy snapshot")
async def energy_callback() -> None:
    """Stub for test_energy_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def energy_initial_state() -> None:
    """Stub for test_energy_initial_state (port deferred)."""

@test.skip("syrupy snapshot")
async def energy_availability() -> None:
    """Stub for test_energy_availability (port deferred)."""
