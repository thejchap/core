"""Tryke skip stub for test_stt.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_transcription_success() -> None:
    """Stub for test_stt_transcription_success."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_transcription_success_auto_language() -> None:
    """Stub for test_stt_transcription_success_auto_language."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_transcription_passes_language_code() -> None:
    """Stub for test_stt_transcription_passes_language_code."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_edge_cases() -> None:
    """Stub for test_stt_edge_cases."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stt_convert_api_error() -> None:
    """Stub for test_stt_convert_api_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def supported_properties() -> None:
    """Stub for test_supported_properties."""

