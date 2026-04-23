"""Common fixtures for Airthings tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from airthings import Airthings
from tryke import fixture

from homeassistant.components.airthings.const import CONF_SECRET, DOMAIN
from homeassistant.const import CONF_ID

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ID: "client_id",
            CONF_SECRET: "secret",
        },
        unique_id="client_id",
    )


@fixture
def mock_airthings_token() -> Generator[Airthings]:
    """Mock an Airthings token."""
    with patch(
        "homeassistant.components.airthings.config_flow.airthings.get_token",
        return_value="test_token",
    ) as mock_get_token:
        yield mock_get_token


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.airthings.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
