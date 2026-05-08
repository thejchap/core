"""Tryke skip stub for test_tts.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak() -> None:
    """Stub for test_tts_service_speak."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_error() -> None:
    """Stub for test_tts_service_speak_error."""

