"""Tryke skip-stubs for openai_conversation stt tests.

Original tests use OpenAI API mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI API mocks + conversation pipeline")
async def stt_entity_properties() -> None:
    """Test STT entity properties."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def stt_process_audio_stream_success_wav() -> None:
    """Test STT processing audio stream successfully."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def stt_process_audio_stream_success_ogg() -> None:
    """Test STT processing audio stream successfully."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def stt_process_audio_stream_api_error() -> None:
    """Test STT processing audio stream with API errors."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def stt_process_audio_stream_empty_response() -> None:
    """Test STT processing with an empty response from the API."""
