"""Tryke skip-stubs for openai_conversation tts tests.

Original tests use OpenAI API mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI API mocks + conversation pipeline")
async def tts() -> None:
    """Test text to speech generation."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def tts_preferred_format() -> None:
    """Test text to speech preferred format handling."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def tts_raw_preferred_format_returns_pcm() -> None:
    """Test raw preferred format is returned as pcm."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def tts_error() -> None:
    """Test exception handling during text to speech generation."""
