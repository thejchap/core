"""Tryke skip stub for test_binary_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the group.binary_sensor module imports cleanly."""
    from homeassistant.components.group import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting_all() -> None:
    """Stub for test_state_reporting_all."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting_any() -> None:
    """Stub for test_state_reporting_any."""

