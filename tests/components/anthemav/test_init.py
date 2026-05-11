"""Test the Anthem A/V Receivers init."""

from collections.abc import Callable
from unittest.mock import ANY, AsyncMock, patch

from anthemav.device_error import DeviceError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from ._fixtures import (
    init_integration,
    mock_anthemav,
    mock_config_entry,
    mock_connection_create,
    update_callback,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_connection_create: AsyncMock = Depends(mock_connection_create),
    mock_anthemav: AsyncMock = Depends(mock_anthemav),
    init_integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test load and unload AnthemAv component."""
    mock_connection_create.assert_called_with(
        host="1.1.1.1", port=14999, update_callback=ANY
    )
    expect(init_integration.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    expect(init_integration.state).to_be(ConfigEntryState.NOT_LOADED)
    mock_anthemav.close.assert_called_once()


@test.cases(
    test.case("oserror", error=OSError),
    test.case("deviceerror", error=DeviceError),
)
async def config_entry_not_ready_when_oserror(
    *,
    error: type[Exception],
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test AnthemAV configuration entry not ready."""
    with patch("anthemav.Connection.create", side_effect=error):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def anthemav_dispatcher_signal(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_connection_create: AsyncMock = Depends(mock_connection_create),
    mock_anthemav: AsyncMock = Depends(mock_anthemav),
    init_integration: MockConfigEntry = Depends(init_integration),
    update_callback: Callable[[str], None] = Depends(update_callback),
) -> None:
    """Test send update signal to dispatcher."""
    states = hass.states.get("media_player.anthem_av")
    expect(states is not None).to_be(True)
    expect(states.state).to_equal(STATE_OFF)

    mock_anthemav.protocol.zones[1].power = True

    update_callback("power")

    await hass.async_block_till_done()

    states = hass.states.get("media_player.anthem_av")
    expect(states.state).to_equal(STATE_ON)
