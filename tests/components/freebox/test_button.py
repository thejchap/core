"""Tryke skip stub for test_button.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the freebox.button module imports cleanly."""
    from homeassistant.components.freebox import button  # noqa: PLC0415
    expect(button).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reboot() -> None:
    """Stub for test_reboot."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def mark_calls_as_read() -> None:
    """Stub for test_mark_calls_as_read."""

