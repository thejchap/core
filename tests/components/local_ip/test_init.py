"""Tests for the local_ip component."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.local_ip.const import DOMAIN
from homeassistant.components.network import MDNS_TARGET_IP, async_get_source_ip
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def basic_setup(hass: HomeAssistant = Depends(hass)) -> None:
    """Test component setup creates entry from config."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state is ConfigEntryState.LOADED).to_be(True)

    local_ip = await async_get_source_ip(hass, target_ip=MDNS_TARGET_IP)
    state = hass.states.get(f"sensor.{DOMAIN}")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(local_ip)

    unload_ok = await hass.config_entries.async_unload(entry.entry_id)
    expect(unload_ok).to_be(True)
    await hass.async_block_till_done()
    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
