"""Tryke fixtures for openexchangerates tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.openexchangerates.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN, data={"api_key": "test-api-key", "base": "USD"}
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.openexchangerates.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_latest_rates_config_flow() -> Generator[AsyncMock]:
    """Mock Client.get_latest."""
    with patch(
        "homeassistant.components.openexchangerates.config_flow.Client.get_latest",
    ) as mock_latest:
        mock_latest.return_value = {"EUR": 1.0}
        yield mock_latest


@fixture
def mock_currencies() -> Generator[AsyncMock]:
    """Mock Client.get_currencies."""
    with patch(
        "homeassistant.components.openexchangerates.config_flow.Client.get_currencies",
        return_value={"USD": "United States Dollar", "EUR": "Euro"},
    ) as mock:
        yield mock
