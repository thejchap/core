"""Tryke fixtures for the smarla integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from pysmarlaapi import AuthToken
from tryke import fixture

from homeassistant.components.smarla.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER

from .const import MOCK_ACCESS_TOKEN_JSON, MOCK_USER_INPUT

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_ACCESS_TOKEN_JSON["serialNumber"],
        source=SOURCE_USER,
        data=MOCK_USER_INPUT,
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Override async_setup_entry."""
    with patch("homeassistant.components.smarla.async_setup_entry", return_value=True):
        yield None


@fixture
def mock_connection() -> Generator[MagicMock]:
    """Patch Connection object."""
    with (
        patch(
            "homeassistant.components.smarla.config_flow.Connection", autospec=True
        ) as mock_connection,
        patch(
            "homeassistant.components.smarla.Connection",
            mock_connection,
        ),
    ):
        connection = mock_connection.return_value

        def mocked_connection(url, token_b64: str):
            connection.token = AuthToken.from_base64(token_b64)
            return connection

        mock_connection.side_effect = mocked_connection

        yield connection
