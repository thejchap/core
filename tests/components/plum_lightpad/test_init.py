"""Tests for the Plum Lightpad config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.plum_lightpad import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, issue_registry, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def repair_issue(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    issue_registry: ir.IssueRegistry = Depends(issue_registry),
) -> None:
    """Test Plum Lightpad repair issue."""

    config_entry_1 = MockConfigEntry(
        title="Example 1",
        domain=DOMAIN,
    )
    config_entry_1.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_1.entry_id)
    await hass.async_block_till_done()
    expect(config_entry_1.state is ConfigEntryState.LOADED).to_be(True)

    config_entry_2 = MockConfigEntry(
        title="Example 2",
        domain=DOMAIN,
    )
    config_entry_2.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_2.state is ConfigEntryState.LOADED).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)

    await hass.config_entries.async_remove(config_entry_1.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(config_entry_2.state is ConfigEntryState.LOADED).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)

    await hass.config_entries.async_remove(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(config_entry_2.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is None).to_be(True)
