"""Tryke fixtures for the broadlink integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_heartbeat() -> Generator[None]:
    """Mock broadlink heartbeat."""
    with patch("homeassistant.components.broadlink.heartbeat.blk.ping"):
        yield


@fixture
def broadlink_setup() -> Generator[None]:
    """Mock broadlink entry setup."""
    with (
        patch("homeassistant.components.broadlink.async_setup", return_value=True),
        patch(
            "homeassistant.components.broadlink.async_setup_entry", return_value=True
        ),
    ):
        yield
