"""Tryke skip stub for test_number.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.number module imports cleanly."""
    from homeassistant.components.fully_kiosk import number  # noqa: PLC0415
    expect(number).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def numbers() -> None:
    """Stub for test_numbers."""

