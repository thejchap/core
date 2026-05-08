"""Tryke skip stub for test_button.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.button module imports cleanly."""
    from homeassistant.components.fully_kiosk import button  # noqa: PLC0415
    expect(button).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""

