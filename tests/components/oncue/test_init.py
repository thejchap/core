"""Tests for the Oncue integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.oncue import DOMAIN
from homeassistant.config_entries import (
    SOURCE_IGNORE,
    ConfigEntryDisabler,
    ConfigEntryState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def oncue_repair_issue(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test the Oncue configuration entry loading/unloading handles the repair."""
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
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)

    config_entry_3 = MockConfigEntry(
        source=SOURCE_IGNORE,
        domain=DOMAIN,
    )
    config_entry_3.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_3.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_3.state).to_be(ConfigEntryState.NOT_LOADED)

    config_entry_4 = MockConfigEntry(
        disabled_by=ConfigEntryDisabler.USER,
        domain=DOMAIN,
    )
    config_entry_4.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_4.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_4.state).to_be(ConfigEntryState.NOT_LOADED)

    await hass.config_entries.async_remove(config_entry_1.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(config_entry_2.state).to_be(ConfigEntryState.LOADED)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)

    await hass.config_entries.async_remove(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(config_entry_2.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN)).to_be(None)

    expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(False)
