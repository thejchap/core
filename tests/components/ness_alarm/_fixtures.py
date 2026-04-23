"""Tryke fixtures for ness_alarm config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.ness_alarm.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 1992,
        },
    )


@fixture
def mock_client() -> Generator[AsyncMock]:
    """Mock the nessclient Client for config flow tests."""
    with patch(
        "homeassistant.components.ness_alarm.config_flow.Client",
        return_value=AsyncMock(),
    ) as mock:
        yield mock.return_value


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.ness_alarm.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def post_connection_delay() -> Generator[None]:
    """Zero out POST_CONNECTION_DELAY for faster tests."""
    with patch(
        "homeassistant.components.ness_alarm.config_flow.POST_CONNECTION_DELAY",
        0,
    ):
        yield
