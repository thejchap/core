"""Tests for the local_ip component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.local_ip.const import DOMAIN
from homeassistant.components.network import MDNS_TARGET_IP, async_get_source_ip
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def basic_setup(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test component setup creates entry from config."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    local_ip = await async_get_source_ip(hass, target_ip=MDNS_TARGET_IP)
    state = hass.states.get(f"sensor.{DOMAIN}")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(local_ip)

    expect(
        await hass.config_entries.async_unload(entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
