"""Tryke fixtures for jewish_calendar integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.jewish_calendar.const import (
    DEFAULT_NAME,
    DOMAIN,
)
from homeassistant.const import CONF_LANGUAGE

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.jewish_calendar.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config_entry() -> MockConfigEntry:
    """Set up the jewish_calendar integration for testing."""
    return MockConfigEntry(
        title=DEFAULT_NAME,
        domain=DOMAIN,
        data={CONF_LANGUAGE: "en"},
        options={},
    )
