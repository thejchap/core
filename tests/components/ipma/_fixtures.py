"""Tryke fixtures for IPMA."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.ipma.const import DOMAIN
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.ipma import MockLocation
from tests.hass_fixtures import hass as hass_fixture


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Home",
            CONF_LATITUDE: 0,
            CONF_LONGITUDE: 0,
        },
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> AsyncGenerator[MockConfigEntry]:
    """Set up the IPMA integration for testing."""
    config_entry.add_to_hass(hass)

    with patch("pyipma.location.Location.get", return_value=MockLocation()):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        yield config_entry
