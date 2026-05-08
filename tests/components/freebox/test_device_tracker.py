"""Tryke skip stub for test_device_tracker.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the freebox.device_tracker module imports cleanly."""
    from homeassistant.components.freebox import device_tracker  # noqa: PLC0415
    expect(device_tracker).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def router_mode() -> None:
    """Stub for test_router_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def bridge_mode() -> None:
    """Stub for test_bridge_mode."""

