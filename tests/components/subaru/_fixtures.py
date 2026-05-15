"""Tryke fixtures for the subaru tests."""

from tryke import Depends, fixture

from homeassistant.components.homeassistant import DOMAIN as HA_DOMAIN
from homeassistant.components.subaru.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

from .conftest import TEST_CONFIG_ENTRY, setup_subaru_config_entry


@fixture
async def subaru_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Create a Subaru config entry prior to setup."""
    await async_setup_component(hass, HA_DOMAIN, {})
    config_entry = MockConfigEntry(**TEST_CONFIG_ENTRY)
    config_entry.add_to_hass(hass)
    return config_entry


@fixture
async def ev_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    subaru_config_entry: MockConfigEntry = Depends(subaru_config_entry),
) -> MockConfigEntry:
    """Create a Subaru entry representing an EV vehicle with full STARLINK subscription."""
    await setup_subaru_config_entry(hass, subaru_config_entry)
    assert DOMAIN in hass.config_entries.async_domains()
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert hass.config_entries.async_get_entry(subaru_config_entry.entry_id)
    assert subaru_config_entry.state is ConfigEntryState.LOADED
    return subaru_config_entry
