"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fritzbox.sensor module imports cleanly."""
    from homeassistant.components.fritzbox import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_error() -> None:
    """Stub for test_update_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discover_new_device() -> None:
    """Stub for test_discover_new_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def next_change_sensors() -> None:
    """Stub for test_next_change_sensors."""

