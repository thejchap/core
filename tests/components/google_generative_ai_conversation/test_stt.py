"""Tryke skip stub for test_stt.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_entity_properties() -> None:
    """Stub for test_stt_entity_properties."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_process_audio_stream_success() -> None:
    """Stub for test_stt_process_audio_stream_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_process_audio_stream_api_error() -> None:
    """Stub for test_stt_process_audio_stream_api_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_process_audio_stream_empty_response() -> None:
    """Stub for test_stt_process_audio_stream_empty_response."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_uses_default_prompt() -> None:
    """Stub for test_stt_uses_default_prompt."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_uses_default_model() -> None:
    """Stub for test_stt_uses_default_model."""

