"""The tests for the WSDOT platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from ._fixtures import (
    mock_config_data,
    mock_config_entry,
    mock_failed_travel_time,
    mock_subentries,
    mock_travel_time,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local anchor fixture (tryke discovery quirk)."""


@test
async def travel_sensor_setup_no_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _failed: None = Depends(mock_failed_travel_time),
    _issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test the wsdot Travel Time sensor does not create an entry with a bad API key."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
