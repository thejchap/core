"""Tests for the Rova integration init."""

from __future__ import annotations

from unittest.mock import MagicMock

from requests import ConnectTimeout
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from . import setup_with_selected_platforms
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_rova as mock_rova_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fx,
    mock_network,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def reload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_rova: MagicMock = Depends(mock_rova_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reloading the integration."""
    await setup_with_selected_platforms(hass, mock_config_entry, [Platform.SENSOR])

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(
        True
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("syrupy snapshot")
async def service() -> None:
    """Stub for test_service (port deferred — uses snapshot)."""


@test.cases(
    test.case("is_rova_area", method="is_rova_area"),
    test.case("get_calendar_items", method="get_calendar_items"),
)
async def retry_after_failure(
    method: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rova: MagicMock = Depends(mock_rova_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we retry after a failure."""
    getattr(mock_rova, method).side_effect = ConnectTimeout
    mock_config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        False
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def issue_if_not_rova_area(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rova: MagicMock = Depends(mock_rova_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
) -> None:
    """Test we create an issue if rova does not collect at the given address."""
    mock_rova.is_rova_area.return_value = False
    mock_config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(
        False
    )
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(len(issue_registry.issues)).to_equal(1)
