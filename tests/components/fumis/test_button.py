"""Tryke skip stub for test_button.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fumis.button module imports cleanly."""
    from homeassistant.components.fumis import button  # noqa: PLC0415
    expect(button).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sync_clock() -> None:
    """Stub for test_sync_clock."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sync_clock_error_handling() -> None:
    """Stub for test_sync_clock_error_handling."""

