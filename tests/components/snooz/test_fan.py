"""Test Snooz fan entity."""

from datetime import timedelta
from unittest.mock import Mock, patch

from pysnooz.api import SnoozDeviceState, UnknownSnoozState
from pysnooz.commands import SnoozCommandResult, SnoozCommandResultStatus
from pysnooz.testing import MockSnoozDevice
from tryke import Depends, expect, fixture, test

from homeassistant.components import fan
from homeassistant.components.snooz.const import (
    ATTR_DURATION,
    DOMAIN,
    SERVICE_TRANSITION_OFF,
    SERVICE_TRANSITION_ON,
)
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import SnoozFixture, create_mock_snooz, create_mock_snooz_config_entry
from ._fixtures import (
    mock_connected_snooz as mock_connected_snooz_fixture,
    snooz_fan_entity_id as snooz_fan_entity_id_fixture,
)

from tests.components.bluetooth import generate_ble_device
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def turn_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test turning on the device."""
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id]},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test
async def transition_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test transitioning on the device."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TRANSITION_ON,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id], ATTR_DURATION: 1},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test.cases(
    test.case("1", percentage=1),
    test.case("22", percentage=22),
    test.case("50", percentage=50),
    test.case("99", percentage=99),
    test.case("100", percentage=100),
)
async def turn_on_with_percentage(
    percentage: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test turning on the device with a percentage."""
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id], fan.ATTR_PERCENTAGE: percentage},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(percentage)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test.cases(
    test.case("1", percentage=1),
    test.case("22", percentage=22),
    test.case("50", percentage=50),
    test.case("99", percentage=99),
    test.case("100", percentage=100),
)
async def set_percentage(
    percentage: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test setting the fan percentage."""
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id], fan.ATTR_PERCENTAGE: percentage},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(percentage)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test
async def set_0_percentage_turns_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test turning off the device by setting the percentage/volume to 0."""
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id], fan.ATTR_PERCENTAGE: 66},
        blocking=True,
    )

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id], fan.ATTR_PERCENTAGE: 0},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    # doesn't overwrite percentage when turning off
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(66)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test
async def turn_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test turning off the device."""
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id]},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test
async def transition_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test transitioning off the device."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TRANSITION_OFF,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id], ATTR_DURATION: 1},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)


@test
async def push_events(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_connected_snooz: SnoozFixture = Depends(mock_connected_snooz_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test state update events from snooz device."""
    mock_connected_snooz.device.trigger_state(SnoozDeviceState(False, 64))

    state = hass.states.get(snooz_fan_entity_id)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(64)

    mock_connected_snooz.device.trigger_state(SnoozDeviceState(True, 12))

    state = hass.states.get(snooz_fan_entity_id)
    expect(ATTR_ASSUMED_STATE not in state.attributes).to_be(True)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(12)

    mock_connected_snooz.device.trigger_disconnect()

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.attributes[ATTR_ASSUMED_STATE]).to_be(True)

    # Don't attempt to reconnect
    await mock_connected_snooz.device.async_disconnect()


@test
async def restore_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Tests restoring entity state."""
    device = await create_mock_snooz(connected=False, initial_state=UnknownSnoozState)

    entry = await create_mock_snooz_config_entry(hass, device)
    entity_id = get_fan_entity_id(hass, device, entity_registry)

    # call service to store state
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id], fan.ATTR_PERCENTAGE: 33},
        blocking=True,
    )

    # unload entry
    await hass.config_entries.async_unload(entry.entry_id)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_UNAVAILABLE)

    # reload entry
    with (
        patch("homeassistant.components.snooz.SnoozDevice", return_value=device),
        patch(
            "homeassistant.components.snooz.async_ble_device_from_address",
            return_value=generate_ble_device(device.address, device.name),
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)

    # should match last known state
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(33)
    expect(state.attributes[ATTR_ASSUMED_STATE]).to_be(True)


@test
async def restore_unknown_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Tests restoring entity state that was unknown."""
    device = await create_mock_snooz(connected=False, initial_state=UnknownSnoozState)

    entry = await create_mock_snooz_config_entry(hass, device)
    entity_id = get_fan_entity_id(hass, device, entity_registry)

    # unload entry
    await hass.config_entries.async_unload(entry.entry_id)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_UNAVAILABLE)

    # reload entry
    with (
        patch("homeassistant.components.snooz.SnoozDevice", return_value=device),
        patch(
            "homeassistant.components.snooz.async_ble_device_from_address",
            return_value=generate_ble_device(device.address, device.name),
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)

    # should match last known state
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def command_results(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_connected_snooz: SnoozFixture = Depends(mock_connected_snooz_fixture),
    snooz_fan_entity_id: str = Depends(snooz_fan_entity_id_fixture),
) -> None:
    """Test device command results."""
    mock_execute = Mock(spec=mock_connected_snooz.device.async_execute_command)

    mock_connected_snooz.device.async_execute_command = mock_execute

    mock_execute.return_value = SnoozCommandResult(
        SnoozCommandResultStatus.SUCCESSFUL, timedelta()
    )
    mock_connected_snooz.device.state = SnoozDeviceState(on=True, volume=56)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id]},
        blocking=True,
    )

    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(56)

    mock_execute.return_value = SnoozCommandResult(
        SnoozCommandResultStatus.CANCELLED, timedelta()
    )
    mock_connected_snooz.device.state = SnoozDeviceState(on=False, volume=15)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [snooz_fan_entity_id]},
        blocking=True,
    )

    # the device state shouldn't be written when cancelled
    state = hass.states.get(snooz_fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(56)

    mock_execute.return_value = SnoozCommandResult(
        SnoozCommandResultStatus.UNEXPECTED_ERROR, timedelta()
    )

    async with expect_raises_async(HomeAssistantError, match="failed with status"):
        await hass.services.async_call(
            fan.DOMAIN,
            fan.SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: [snooz_fan_entity_id]},
            blocking=True,
        )


def get_fan_entity_id(
    hass: HomeAssistant, device: MockSnoozDevice, entity_registry: er.EntityRegistry
) -> str:
    """Get the entity ID for a mock device."""
    return entity_registry.async_get_entity_id(Platform.FAN, DOMAIN, device.address)
