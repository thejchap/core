"""The tests for the Canary alarm_control_panel platform."""

from unittest.mock import MagicMock, PropertyMock, patch

from canary.const import LOCATION_MODE_AWAY, LOCATION_MODE_HOME, LOCATION_MODE_NIGHT
from tryke import Depends, expect, fixture, test

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_DOMAIN,
    AlarmControlPanelState,
)
from homeassistant.const import (
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity

from . import init_integration, mock_device, mock_location, mock_mode
from ._fixtures import canary, mock_ffmpeg

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ffmpeg: None = Depends(mock_ffmpeg),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def alarm_control_panel(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test the creation and values of the alarm_control_panel for Canary."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    mocked_location = mock_location(
        location_id=100,
        name="Home",
        is_celsius=True,
        is_private=False,
        mode=mock_mode(7, "standby"),
        devices=[online_device_at_home],
    )

    instance = canary.return_value
    instance.get_locations.return_value = [mocked_location]

    with patch("homeassistant.components.canary.PLATFORMS", ["alarm_control_panel"]):
        await init_integration(hass)

    entity_id = "alarm_control_panel.home"
    entity_entry = entity_registry.async_get(entity_id)
    expect(entity_entry).not_.to_be(None)
    expect(entity_entry.unique_id).to_equal("100")

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(bool(state.attributes["private"])).to_be(False)

    # test private system
    type(mocked_location).is_private = PropertyMock(return_value=True)

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.DISARMED)
    expect(bool(state.attributes["private"])).to_be(True)

    type(mocked_location).is_private = PropertyMock(return_value=False)

    # test armed home
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(4, LOCATION_MODE_HOME)
    )

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_HOME)

    # test armed away
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(5, LOCATION_MODE_AWAY)
    )

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_AWAY)

    # test armed night
    type(mocked_location).mode = PropertyMock(
        return_value=mock_mode(6, LOCATION_MODE_NIGHT)
    )

    await async_update_entity(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(AlarmControlPanelState.ARMED_NIGHT)


@test
async def alarm_control_panel_services(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    canary: MagicMock = Depends(canary),
) -> None:
    """Test the services of the alarm_control_panel for Canary."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    mocked_location = mock_location(
        location_id=100,
        name="Home",
        is_celsius=True,
        mode=mock_mode(1, "disarmed"),
        devices=[online_device_at_home],
    )

    instance = canary.return_value
    instance.get_locations.return_value = [mocked_location]

    with patch("homeassistant.components.canary.PLATFORMS", ["alarm_control_panel"]):
        await init_integration(hass)

    entity_id = "alarm_control_panel.home"

    # test arm away
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_AWAY,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, LOCATION_MODE_AWAY)

    # test arm home
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_HOME,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, LOCATION_MODE_HOME)

    # test arm night
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_ARM_NIGHT,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, LOCATION_MODE_NIGHT)

    # test disarm
    await hass.services.async_call(
        ALARM_DOMAIN,
        SERVICE_ALARM_DISARM,
        service_data={"entity_id": entity_id},
        blocking=True,
    )
    instance.set_location_mode.assert_called_with(100, "disarmed", True)
