"""Tryke skip stub for test_device_tracker.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fressnapf_tracker.device_tracker module imports cleanly."""
    from homeassistant.components.fressnapf_tracker import device_tracker  # noqa: PLC0415
    expect(device_tracker).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_entity_device_snapshots() -> None:
    """Stub for test_state_entity_device_snapshots."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_tracker_no_position() -> None:
    """Stub for test_device_tracker_no_position."""

