"""Tryke fixtures for the 1-Wire integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.onewire.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.onewire.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config_entry() -> MockConfigEntry:
    """Mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
        },
        options={
            "device_options": {
                "28.222222222222": {"precision": "temperature9"},
                "28.222222222223": {"precision": "temperature5"},
            }
        },
        entry_id="2",
    )
