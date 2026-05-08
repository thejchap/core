"""Tests for the RDW integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from vehicle import RDWConnectionError, RDWError

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_rdw

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _rdw: MagicMock = Depends(mock_rdw),
) -> None:
    """Test the RDW configuration entry loading/unloading."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("connection_error", side_effect=RDWConnectionError),
    test.case("rdw_error", side_effect=RDWError),
)
async def config_entry_not_ready(
    side_effect: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    rdw: MagicMock = Depends(mock_rdw),
) -> None:
    """Test the RDW configuration entry not ready."""
    rdw.vehicle.side_effect = side_effect

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(rdw.vehicle.call_count).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
