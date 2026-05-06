"""Tryke fixtures for the Radio Browser integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.radio_browser.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My Radios",
        domain=DOMAIN,
        data={},
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.radio_browser.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
