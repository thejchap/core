"""Tryke skip stub for test_notify.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.notify module imports cleanly."""
    from homeassistant.components.fully_kiosk import notify  # noqa: PLC0415
    expect(notify).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_text_to_speech() -> None:
    """Stub for test_notify_text_to_speech."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_text_to_speech_raises() -> None:
    """Stub for test_notify_text_to_speech_raises."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_overlay_message() -> None:
    """Stub for test_notify_overlay_message."""

