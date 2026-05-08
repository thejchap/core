"""Tryke skip stub for test_tts.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_success() -> None:
    """Stub for test_tts_service_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_rate_limited() -> None:
    """Stub for test_tts_rate_limited."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_missing_voice_id() -> None:
    """Stub for test_tts_missing_voice_id."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_supported_languages() -> None:
    """Stub for test_tts_supported_languages."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak() -> None:
    """Stub for test_tts_service_speak."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_with_language() -> None:
    """Stub for test_tts_service_speak_with_language."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_server_error() -> None:
    """Stub for test_tts_service_speak_server_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_rate_limit_error() -> None:
    """Stub for test_tts_service_speak_rate_limit_error."""

