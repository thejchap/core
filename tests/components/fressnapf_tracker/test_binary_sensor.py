"""Tryke skip stub for test_binary_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fressnapf_tracker.binary_sensor module imports cleanly."""
    from homeassistant.components.fressnapf_tracker import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_entity_device_snapshots() -> None:
    """Stub for test_state_entity_device_snapshots."""

