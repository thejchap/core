"""Test the Sunricher DALI binary sensor platform. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.sunricher_dali.binary_sensor module imports cleanly."""
    from homeassistant.components.sunricher_dali import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("syrupy snapshot")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_initial_state() -> None:
    """Stub for test_occupancy_sensor_initial_state (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_motion_detected() -> None:
    """Stub for test_occupancy_sensor_motion_detected (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_presence_detected() -> None:
    """Stub for test_occupancy_sensor_presence_detected (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_occupancy_detected() -> None:
    """Stub for test_occupancy_sensor_occupancy_detected (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_ignores_no_motion() -> None:
    """Stub for test_occupancy_sensor_ignores_no_motion (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_vacant() -> None:
    """Stub for test_occupancy_sensor_vacant (port deferred)."""

@test.skip("syrupy snapshot")
async def occupancy_sensor_availability() -> None:
    """Stub for test_occupancy_sensor_availability (port deferred)."""

@test.skip("syrupy snapshot")
async def motion_sensor_initial_state() -> None:
    """Stub for test_motion_sensor_initial_state (port deferred)."""

@test.skip("syrupy snapshot")
async def motion_sensor_on_motion() -> None:
    """Stub for test_motion_sensor_on_motion (port deferred)."""

@test.skip("syrupy snapshot")
async def motion_sensor_off_no_motion() -> None:
    """Stub for test_motion_sensor_off_no_motion (port deferred)."""

@test.skip("syrupy snapshot")
async def motion_sensor_ignores_occupancy_events() -> None:
    """Stub for test_motion_sensor_ignores_occupancy_events (port deferred)."""
