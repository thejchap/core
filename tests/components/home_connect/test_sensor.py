"""Tryke skip-stubs for test_sensor.py - indirect parametrize unsupported."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the home_connect integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.home_connect.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("home_connect")


@test.skip("indirect parametrize unsupported")
async def paired_depaired_devices_flow() -> None:
    """Stub for test_paired_depaired_devices_flow."""

@test.skip("indirect parametrize unsupported")
async def connected_devices() -> None:
    """Stub for test_connected_devices."""

@test.skip("indirect parametrize unsupported")
async def sensor_entity_availability() -> None:
    """Stub for test_sensor_entity_availability."""

@test.skip("indirect parametrize unsupported")
async def program_sensors() -> None:
    """Stub for test_program_sensors."""

@test.skip("indirect parametrize unsupported")
async def program_sensor_edge_case() -> None:
    """Stub for test_program_sensor_edge_case."""

@test.skip("indirect parametrize unsupported")
async def remaining_prog_time_edge_cases() -> None:
    """Stub for test_remaining_prog_time_edge_cases."""

@test.skip("indirect parametrize unsupported")
async def sensors_states() -> None:
    """Stub for test_sensors_states."""

@test.skip("indirect parametrize unsupported")
async def sensor_unit_fetching() -> None:
    """Stub for test_sensor_unit_fetching."""

@test.skip("indirect parametrize unsupported")
async def sensor_unit_fetching_error() -> None:
    """Stub for test_sensor_unit_fetching_error."""

@test.skip("indirect parametrize unsupported")
async def sensor_unit_fetching_after_rate_limit_error() -> None:
    """Stub for test_sensor_unit_fetching_after_rate_limit_error."""
