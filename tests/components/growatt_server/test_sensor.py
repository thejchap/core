"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the growatt_server integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.growatt_server.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("growatt_server")


@test.skip("requires mock_growatt_v1_api fixture + syrupy snapshot")
async def sph_sensors_v1_api() -> None:
    """Stub for test_sph_sensors_v1_api."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sph_sensor_unavailable_on_coordinator_error() -> None:
    """Stub for test_sph_sensor_unavailable_on_coordinator_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def min_sensors_v1_api() -> None:
    """Stub for test_min_sensors_v1_api."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_classic_api() -> None:
    """Stub for test_sensors_classic_api."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_coordinator_updates() -> None:
    """Stub for test_sensor_coordinator_updates."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_unavailable_on_coordinator_error() -> None:
    """Stub for test_sensor_unavailable_on_coordinator_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def midnight_bounce_suppression() -> None:
    """Stub for test_midnight_bounce_suppression."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def normal_reset_no_bounce() -> None:
    """Stub for test_normal_reset_no_bounce."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def midnight_bounce_repeated() -> None:
    """Stub for test_midnight_bounce_repeated."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def non_total_increasing_sensor_unaffected_by_bounce_suppression() -> None:
    """Stub for test_non_total_increasing_sensor_unaffected_by_bounce_suppression."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def total_sensors_classic_api() -> None:
    """Stub for test_total_sensors_classic_api."""

