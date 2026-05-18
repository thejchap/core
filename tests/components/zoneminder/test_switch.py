"""Tests for ZoneMinder switch entities."""

from datetime import timedelta
from unittest.mock import MagicMock

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
import voluptuous as vol
from zoneminder.monitor import MonitorState

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.zoneminder.const import DOMAIN
from homeassistant.components.zoneminder.switch import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_zoneminder_client, single_server_config, two_monitors
from .conftest import create_mock_monitor

from tests.common import async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


async def _setup_zm_with_switches(
    hass: HomeAssistant,
    mock_zoneminder_client: MagicMock,
    zm_config: dict,
    monitors: list,
    freezer: FrozenDateTimeFactory,
    command_on: str = "Modect",
    command_off: str = "Monitor",
) -> None:
    """Set up ZM component with switch platform and trigger first poll."""
    mock_zoneminder_client.get_monitors.return_value = monitors

    expect(await async_setup_component(hass, DOMAIN, zm_config)).to_be_truthy()
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(
        await async_setup_component(
            hass,
            SWITCH_DOMAIN,
            {
                SWITCH_DOMAIN: [
                    {
                        "platform": DOMAIN,
                        "command_on": command_on,
                        "command_off": command_off,
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done(wait_background_tasks=True)
    # Trigger first poll to update entity state
    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


@test
async def switch_per_monitor(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    two_monitors: list = Depends(two_monitors),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test one switch entity is created per monitor."""
    await _setup_zm_with_switches(
        hass, mock_zoneminder_client, single_server_config, two_monitors, freezer
    )

    states = hass.states.async_all(SWITCH_DOMAIN)
    expect(len(states)).to_equal(2)


@test
async def switch_name_format(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test switch name format is '{name} State'."""
    monitors = [create_mock_monitor(name="Front Door")]
    await _setup_zm_with_switches(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("switch.front_door_state")
    expect(state).not_.to_be_none()
    expect(state.name).to_equal("Front Door State")


@test
async def switch_on_when_function_matches_command_on(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test switch is ON when monitor function matches command_on."""
    monitors = [create_mock_monitor(name="Front Door", function=MonitorState.MODECT)]
    await _setup_zm_with_switches(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        command_on="Modect",
    )

    state = hass.states.get("switch.front_door_state")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_ON)


@test
async def switch_off_when_function_differs(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test switch is OFF when monitor function differs from command_on."""
    monitors = [create_mock_monitor(name="Front Door", function=MonitorState.MONITOR)]
    await _setup_zm_with_switches(
        hass,
        mock_zoneminder_client,
        single_server_config,
        monitors,
        freezer,
        command_on="Modect",
    )

    state = hass.states.get("switch.front_door_state")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_OFF)


@test
async def switch_turn_on_service(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test turn_on service sets monitor function to command_on."""
    monitors = [create_mock_monitor(name="Front Door", function=MonitorState.MONITOR)]
    await _setup_zm_with_switches(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.front_door_state"},
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(monitors[0].function).to_equal(MonitorState("Modect"))


@test
async def switch_turn_off_service(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test turn_off service sets monitor function to command_off."""
    monitors = [create_mock_monitor(name="Front Door", function=MonitorState.MODECT)]
    await _setup_zm_with_switches(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.front_door_state"},
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(monitors[0].function).to_equal(MonitorState("Monitor"))


@test
async def switch_icon(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test switch icon is mdi:record-rec."""
    monitors = [create_mock_monitor(name="Front Door")]
    await _setup_zm_with_switches(
        hass, mock_zoneminder_client, single_server_config, monitors, freezer
    )

    state = hass.states.get("switch.front_door_state")
    expect(state).not_.to_be_none()
    expect(state.attributes.get("icon")).to_equal("mdi:record-rec")


@test
async def switch_platform_not_ready_empty_monitors(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_zoneminder_client: MagicMock = Depends(mock_zoneminder_client),
    single_server_config: dict = Depends(single_server_config),
) -> None:
    """Test PlatformNotReady on empty monitors."""
    mock_zoneminder_client.get_monitors.return_value = []

    expect(
        await async_setup_component(hass, DOMAIN, single_server_config)
    ).to_be_truthy()
    await hass.async_block_till_done()
    await async_setup_component(
        hass,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: [
                {
                    "platform": DOMAIN,
                    "command_on": "Modect",
                    "command_off": "Monitor",
                }
            ]
        },
    )
    await hass.async_block_till_done()

    states = hass.states.async_all(SWITCH_DOMAIN)
    expect(len(states)).to_equal(0)


@test
def platform_schema_requires_command_on_off() -> None:
    """Test platform schema requires command_on and command_off."""
    # Missing command_on
    expect(
        lambda: PLATFORM_SCHEMA({"platform": "zoneminder", "command_off": "Monitor"})
    ).to_raise(vol.MultipleInvalid)

    # Missing command_off
    expect(
        lambda: PLATFORM_SCHEMA({"platform": "zoneminder", "command_on": "Modect"})
    ).to_raise(vol.MultipleInvalid)
