"""Tryke fixtures for Swiss public transport tests."""

from __future__ import annotations

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.swiss_public_transport.const import (
    CONF_DESTINATION,
    CONF_START,
    DOMAIN,
)

from .conftest import DESTINATION, START

from tests.common import MockConfigEntry, load_fixture


@fixture
def mock_opendata_client() -> Generator[AsyncMock]:
    """Mock an Opendata client."""
    with (
        patch(
            "homeassistant.components.swiss_public_transport.OpendataTransport",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.swiss_public_transport.config_flow.OpendataTransport",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.async_get_data.return_value = None
        client.from_name = START
        client.to_name = DESTINATION
        client.connections = json.loads(load_fixture("connections.json", DOMAIN))[0:3]
        yield client


@fixture
def swiss_public_transport_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_START: START,
            CONF_DESTINATION: DESTINATION,
        },
        title=f"{START} {DESTINATION}",
        entry_id="01JBVVVJ87F6G5V0QJX6HBC94T",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.swiss_public_transport.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock
