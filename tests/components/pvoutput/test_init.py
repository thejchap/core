"""Tests for the PVOutput integration."""

from __future__ import annotations

from unittest.mock import MagicMock

from pvo import (
    PVOutputAuthenticationError,
    PVOutputConnectionError,
    PVOutputError,
    PVOutputNoDataError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.pvoutput.const import DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_pvoutput as mock_pvoutput_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
) -> None:
    """Test the PVOutput configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_pvoutput.status.mock_calls)).to_equal(1)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("connection_error", side_effect=PVOutputConnectionError),
    test.case("no_data_error", side_effect=PVOutputNoDataError),
    test.case("generic_error", side_effect=PVOutputError),
)
async def config_entry_not_ready(
    side_effect: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
) -> None:
    """Test the PVOutput configuration entry not ready."""
    mock_pvoutput.status.side_effect = side_effect

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(len(mock_pvoutput.status.mock_calls)).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_authentication_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
) -> None:
    """Test trigger reauthentication flow."""
    mock_config_entry.add_to_hass(hass)

    mock_pvoutput.status.side_effect = PVOutputAuthenticationError

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be(True)
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(mock_config_entry.entry_id)
