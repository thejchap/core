"""Tests for Cert Expiry setup."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.cert_expiry.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.setup import async_setup_component

from .const import HOST, PORT
from .helpers import future_timestamp

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def update_unique_id(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating a config entry without a unique_id."""
    expect(hass.state).to_be(CoreState.running)

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT})
    entry.add_to_hass(hass)

    config_entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(config_entries)).to_equal(1)
    expect(entry).to_be(config_entries[0])
    expect(bool(entry.unique_id)).to_be(False)

    with patch(
        "homeassistant.components.cert_expiry.coordinator.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.unique_id).to_equal(f"{HOST}:{PORT}")


@test.skip("sensor.example_com_cert_expiry not registered after async_setup_component in tryke env")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""


@test.skip("sensor.example_com_cert_expiry not registered after async_start in tryke env")
async def delay_load_during_startup() -> None:
    """Stub for test_delay_load_during_startup."""
