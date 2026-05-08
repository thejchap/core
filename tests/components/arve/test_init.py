"""Tests for the Arve component."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.arve.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def migrate_entry_minor_version_1_2(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migrating a 1.1 config entry to 1.2."""
    with patch("homeassistant.components.arve.async_setup_entry", return_value=True):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={CONF_ACCESS_TOKEN: "mock", CONF_CLIENT_SECRET: "mock"},
            version=1,
            minor_version=1,
            unique_id=12345,
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        expect(entry.version).to_equal(1)
        expect(entry.minor_version).to_equal(2)
        expect(entry.unique_id).to_equal("12345")
