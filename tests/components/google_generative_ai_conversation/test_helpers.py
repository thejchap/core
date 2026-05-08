"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def parse_audio_mime_type_uppercase() -> None:
    """Stub for test_parse_audio_mime_type_uppercase."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def parse_audio_mime_type_lowercase() -> None:
    """Stub for test_parse_audio_mime_type_lowercase."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def parse_audio_mime_type_unsupported_raises() -> None:
    """Stub for test_parse_audio_mime_type_unsupported_raises."""

