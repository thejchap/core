"""Tests for the initialization of the A. O. Smith integration."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from py_aosmith import AOSmithUnknownException
from tryke import Depends, expect, fixture, test

from homeassistant.components.aosmith.const import (
    DOMAIN,
    FAST_INTERVAL,
    REGULAR_INTERVAL,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    init_integration as init_integration_fixture,
    mock_client as mock_client_fixture,
    mock_config_entry as mock_config_entry_fixture,
)
from .conftest import build_device_fixture

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def config_entry_setup(
    _hass: HomeAssistant = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test setup of the config entry."""
    expect(init_integration.state).to_be(ConfigEntryState.LOADED)


@test
async def config_entry_not_ready_get_devices_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test the config entry not ready when get_devices fails."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
        side_effect=AOSmithUnknownException("Unknown error"),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_not_ready_get_energy_use_data_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test the config entry not ready when get_energy_use_data fails."""
    mock_config_entry.add_to_hass(hass)

    get_devices_fixture = [
        build_device_fixture(
            heat_pump=True,
            mode_pending=False,
            setpoint_pending=False,
            has_vacation_mode=True,
            supports_hot_water_plus=False,
        )
    ]

    with (
        patch(
            "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_devices",
            return_value=get_devices_fixture,
        ),
        patch(
            "homeassistant.components.aosmith.config_flow.AOSmithAPIClient.get_energy_use_data",
            side_effect=AOSmithUnknownException("Unknown error"),
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("indirect parametrize on get_devices_fixture_* not supported in tryke 0.0.27")
async def update(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: MagicMock = Depends(mock_client_fixture),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    *,
    time_to_wait: timedelta,
    expected_call_count: int,
) -> None:
    """Test data update with differing intervals depending on device status."""
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].state).to_be(ConfigEntryState.LOADED)
    expect(mock_client.get_devices.call_count).to_equal(1)

    freezer.tick(time_to_wait)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(mock_client.get_devices.call_count).to_equal(1 + expected_call_count)
