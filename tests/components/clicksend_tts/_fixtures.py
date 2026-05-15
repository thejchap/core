"""Tryke fixtures for the clicksend_tts integration tests."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_clicksend_tts_notify() -> Generator:
    """Mock Clicksend TTS notify service."""
    with patch(
        "homeassistant.components.clicksend_tts.notify.get_service", autospec=True
    ) as ns:
        yield ns
