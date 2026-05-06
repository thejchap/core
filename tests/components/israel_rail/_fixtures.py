"""Tryke fixtures for the israel_rail integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.israel_rail import CONF_DESTINATION, CONF_START, DOMAIN

from tests.common import MockConfigEntry

from .conftest import TRAINS

VALID_CONFIG = {
    CONF_START: "באר יעקב",
    CONF_DESTINATION: "אשקלון",
}

SOURCE_DEST = "באר יעקב אשקלון"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.israel_rail.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
        unique_id=SOURCE_DEST,
    )


@fixture
def mock_israelrail() -> Generator[AsyncMock]:
    """Build a fixture for the Israel rail API."""
    with (
        patch(
            "homeassistant.components.israel_rail.TrainSchedule",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.israel_rail.config_flow.TrainSchedule",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.query.return_value = TRAINS

        yield client
