"""Tryke fixtures for the Acmeda integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.acmeda.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_hub_run() -> Generator[AsyncMock]:
    """Mock the hub run method."""
    with patch("homeassistant.components.acmeda.hub.aiopulse.Hub.run") as mock_run:
        yield mock_run


@fixture
def mock_hub_discover() -> Generator[object]:
    """Mock the hub discover method."""
    with patch("aiopulse.Hub.discover") as mock_discover:
        yield mock_discover


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "127.0.0.1"},
    )
    mock_config_entry.add_to_hass(hass)
    return mock_config_entry
