"""Tryke skip stub for test_tts.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_generative_ai_conversation.tts module imports cleanly."""
    from homeassistant.components.google_generative_ai_conversation import tts  # noqa: PLC0415
    expect(tts).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak() -> None:
    """Stub for test_tts_service_speak."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_error() -> None:
    """Stub for test_tts_service_speak_error."""

