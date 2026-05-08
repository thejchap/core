"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_text_to_speech() -> None:
    """Stub for test_notify_text_to_speech."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_text_to_speech_raises() -> None:
    """Stub for test_notify_text_to_speech_raises."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_overlay_message() -> None:
    """Stub for test_notify_overlay_message."""

