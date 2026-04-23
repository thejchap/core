"""Tryke fixtures for myStrom config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.mystrom.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

DEVICE_NAME = "myStrom Device"
DEVICE_MAC = "6001940376EB"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.mystrom.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config_entry(hass: HomeAssistant = Depends(hass_fixture)) -> MockConfigEntry:
    """Create and add a config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE_MAC,
        data={CONF_HOST: "1.1.1.1"},
        title=DEVICE_NAME,
    )
    config_entry.add_to_hass(hass)
    return config_entry
