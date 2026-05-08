"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the glances.sensor module imports cleanly."""
    from homeassistant.components.glances import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_states() -> None:
    """Stub for test_sensor_states."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def uptime_variation() -> None:
    """Stub for test_uptime_variation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_removed() -> None:
    """Stub for test_sensor_removed."""

