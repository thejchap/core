"""Tryke skip stub for test_tts.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak() -> None:
    """Stub for test_tts_service_speak."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_lang_config() -> None:
    """Stub for test_tts_service_speak_lang_config."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_error() -> None:
    """Stub for test_tts_service_speak_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_voice_settings() -> None:
    """Stub for test_tts_service_speak_voice_settings."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tts_service_speak_without_options() -> None:
    """Stub for test_tts_service_speak_without_options."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stream_tts_with_request_ids() -> None:
    """Stub for test_stream_tts_with_request_ids."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stream_tts_without_previous_info() -> None:
    """Stub for test_stream_tts_without_previous_info."""

