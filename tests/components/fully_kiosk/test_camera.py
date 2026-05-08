"""Tryke skip stub for test_camera.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.camera module imports cleanly."""
    from homeassistant.components.fully_kiosk import camera  # noqa: PLC0415
    expect(camera).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def camera() -> None:
    """Stub for test_camera."""

