"""Tryke skip stub for test_image.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.image module imports cleanly."""
    from homeassistant.components.fully_kiosk import image  # noqa: PLC0415
    expect(image).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def image() -> None:
    """Stub for test_image."""

