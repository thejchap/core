"""Tests for the Mazda Connected Services integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.mazda import DOMAIN
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
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def mazda_repair_issue(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test the Mazda configuration entry loading/unloading handles the repair."""
    config_entry_1 = MockConfigEntry(
        title="Example 1",
        domain=DOMAIN,
    )
    config_entry_1.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_1.entry_id)
    await hass.async_block_till_done()
    expect(config_entry_1.state is ConfigEntryState.LOADED).to_be(True)

    # Add a second one
    config_entry_2 = MockConfigEntry(
        title="Example 2",
        domain=DOMAIN,
    )
    config_entry_2.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_2.state is ConfigEntryState.LOADED).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)

    # Add an ignored entry
    config_entry_3 = MockConfigEntry(
        source=SOURCE_IGNORE,
        domain=DOMAIN,
    )
    config_entry_3.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_3.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_3.state is ConfigEntryState.NOT_LOADED).to_be(True)

    # Add a disabled entry
    config_entry_4 = MockConfigEntry(
        disabled_by=ConfigEntryDisabler.USER,
        domain=DOMAIN,
    )
    config_entry_4.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry_4.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_4.state is ConfigEntryState.NOT_LOADED).to_be(True)

    # Remove the first one
    await hass.config_entries.async_remove(config_entry_1.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(config_entry_2.state is ConfigEntryState.LOADED).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is not None).to_be(True)

    # Remove the second one
    await hass.config_entries.async_remove(config_entry_2.entry_id)
    await hass.async_block_till_done()

    expect(config_entry_1.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(config_entry_2.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, DOMAIN) is None).to_be(True)

    # Check the ignored and disabled entries are removed
    expect(bool(hass.config_entries.async_entries(DOMAIN))).to_be(False)
