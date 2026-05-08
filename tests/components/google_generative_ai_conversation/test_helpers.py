"""Tryke skip stub for test_helpers.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_generative_ai_conversation.helpers module imports cleanly."""
    from homeassistant.components.google_generative_ai_conversation import helpers  # noqa: PLC0415
    expect(helpers).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def parse_audio_mime_type_uppercase() -> None:
    """Stub for test_parse_audio_mime_type_uppercase."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def parse_audio_mime_type_lowercase() -> None:
    """Stub for test_parse_audio_mime_type_lowercase."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def parse_audio_mime_type_unsupported_raises() -> None:
    """Stub for test_parse_audio_mime_type_unsupported_raises."""

