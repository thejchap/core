"""Tests for the JuiceNet component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.juicenet import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def juicenet_repair_issue(
    hass: HomeAssistant = Depends(_trigger_executor),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test the JuiceNet configuration entry loading/unloading handles the repair."""
    config_entry_1 = MockConfigEntry(
        title="Example 1",
        domain=DOMAIN,
    )
    config_entry_1.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_1.entry_id)
    await hass.async_block_till_done()
    expect(config_entry_1.state).to_be(ConfigEntryState.LOADED)

    config_entry_2 = MockConfigEntry(
        title="Example 2",
        domain=DOMAIN,
    )
    config_entry_2.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_2.state).to_be(ConfigEntryState.LOADED)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN)).not_.to_be(None)

    await hass.config_entries.async_remove(config_entry_1.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(config_entry_2.state).to_be(ConfigEntryState.LOADED)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN)).not_.to_be(None)

    await hass.config_entries.async_remove(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(config_entry_2.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN)).to_be(None)
