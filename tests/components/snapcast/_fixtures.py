"""Tryke fixtures for snapcast config flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from snapcast.control.server import CONTROL_PORT
from tryke import Depends, fixture

from homeassistant.components.snapcast.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.snapcast.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_create_server() -> Generator[AsyncMock]:
    """Create mock snapcast connection (minimal for config flow)."""
    with patch(
        "homeassistant.components.snapcast.coordinator.Snapserver", autospec=True
    ) as mock_snapserver:
        mock_server = mock_snapserver.return_value
        mock_server.groups = []
        mock_server.clients = []
        mock_server.streams = []
        yield mock_server


@fixture
def mock_server(
    create_server: AsyncMock = Depends(mock_create_server),
) -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.snapcast.config_flow.snapcast.control.create_server",
        return_value=create_server,
    ) as mock_server:
        yield mock_server


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: CONTROL_PORT,
        },
    )
