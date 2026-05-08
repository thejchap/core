"""Tryke fixtures for the Satel Integra integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override integration setup."""
    with patch(
        "homeassistant.components.satel_integra.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_satel() -> Generator[AsyncMock]:
    """Mock the AsyncSatel client used by the config flow."""
    with (
        patch(
            "homeassistant.components.satel_integra.client.AsyncSatel",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.satel_integra.config_flow.AsyncSatel",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value

        client.partition_states = {}
        client.violated_outputs = []
        client.violated_zones = []

        client.connect = AsyncMock(return_value=True)
        client.set_output = AsyncMock()
        client.register_callbacks = MagicMock()
        client.start = AsyncMock()

        yield client
