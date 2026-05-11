"""Tests for the Google Generative AI Conversation helpers."""

from tryke import expect, test

from homeassistant.components.google_generative_ai_conversation.helpers import (
    _parse_audio_mime_type,
)
from homeassistant.exceptions import HomeAssistantError


@test
def parse_audio_mime_type_uppercase() -> None:
    """Test parsing uppercase MIME type audio/L16;rate=24000."""
    result = _parse_audio_mime_type("audio/L16;rate=24000")
    expect(result).to_equal({"bits_per_sample": 16, "rate": 24000})


@test
def parse_audio_mime_type_lowercase() -> None:
    """Test parsing lowercase MIME type audio/l16; rate=24000; channels=1."""
    result = _parse_audio_mime_type("audio/l16; rate=24000; channels=1")
    expect(result).to_equal({"bits_per_sample": 16, "rate": 24000})


@test
def parse_audio_mime_type_unsupported_raises() -> None:
    """Test that an unsupported MIME type raises HomeAssistantError."""
    expect(lambda: _parse_audio_mime_type("video/mp4")).to_raise(HomeAssistantError)
