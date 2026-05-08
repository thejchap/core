"""Tryke skip stub for test_binary_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the freebox.binary_sensor module imports cleanly."""
    from homeassistant.components.freebox import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raid_array_degraded() -> None:
    """Stub for test_raid_array_degraded."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def home() -> None:
    """Stub for test_home."""

