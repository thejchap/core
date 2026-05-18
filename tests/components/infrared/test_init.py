"""Tests for the Infrared integration setup."""

from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from infrared_protocols import NECCommand
from tryke import Depends, expect, fixture, test

from homeassistant.components.infrared import (
    DATA_COMPONENT,
    DOMAIN,
    async_get_emitters,
    async_send_command,
)
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import (
    MockInfraredEntity,
    init_integration as init_integration_fixture,
    mock_infrared_entity as mock_infrared_entity_fixture,
)

from tests.common import mock_restore_cache
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test
async def get_entities_integration_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting entities when the integration is not setup."""
    expect(async_get_emitters(hass)).to_equal([])


@test
async def get_entities_empty(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_integration_fixture),
) -> None:
    """Test getting entities when none are registered."""
    expect(async_get_emitters(hass)).to_equal([])


@test
async def infrared_entity_initial_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_integration_fixture),
    mock_infrared_entity: MockInfraredEntity = Depends(mock_infrared_entity_fixture),
) -> None:
    """Test infrared entity has no state before any command is sent."""
    component = hass.data[DATA_COMPONENT]
    await component.async_add_entities([mock_infrared_entity])

    state = hass.states.get("infrared.test_ir_transmitter")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def async_send_command_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_integration_fixture),
    mock_infrared_entity: MockInfraredEntity = Depends(mock_infrared_entity_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test sending command via async_send_command helper."""
    component = hass.data[DATA_COMPONENT]
    await component.async_add_entities([mock_infrared_entity])

    now = dt_util.utcnow()
    freezer.move_to(now)

    command = NECCommand(address=0x04FB, command=0x08F7, modulation=38000)
    await async_send_command(hass, mock_infrared_entity.entity_id, command)

    expect(len(mock_infrared_entity.send_command_calls)).to_equal(1)
    expect(mock_infrared_entity.send_command_calls[0]).to_be(command)

    state = hass.states.get("infrared.test_ir_transmitter")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(now.isoformat(timespec="milliseconds"))


@test
async def async_send_command_error_does_not_update_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_integration_fixture),
    mock_infrared_entity: MockInfraredEntity = Depends(mock_infrared_entity_fixture),
) -> None:
    """Test that state is not updated when async_send_command raises an error."""
    component = hass.data[DATA_COMPONENT]
    await component.async_add_entities([mock_infrared_entity])

    state = hass.states.get("infrared.test_ir_transmitter")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)

    command = NECCommand(address=0x04FB, command=0x08F7, modulation=38000)

    mock_infrared_entity.async_send_command = AsyncMock(
        side_effect=HomeAssistantError("Transmission failed")
    )

    async with expect_raises_async(HomeAssistantError, match="Transmission failed"):
        await async_send_command(hass, mock_infrared_entity.entity_id, command)

    state = hass.states.get("infrared.test_ir_transmitter")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def async_send_command_entity_not_found(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_integration_fixture),
) -> None:
    """Test async_send_command raises error when entity not found."""
    command = NECCommand(
        address=0x04FB, command=0x08F7, modulation=38000, repeat_count=1
    )

    async with expect_raises_async(
        HomeAssistantError,
        match="entity_not_found",
    ):
        await async_send_command(hass, "infrared.nonexistent_entity", command)


@test
async def async_send_command_component_not_loaded(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_send_command raises error when component not loaded."""
    command = NECCommand(
        address=0x04FB, command=0x08F7, modulation=38000, repeat_count=1
    )

    async with expect_raises_async(HomeAssistantError, match="component_not_loaded"):
        await async_send_command(hass, "infrared.some_entity", command)


@test.cases(
    test.case(
        "restored_timestamp",
        restored_value="2026-01-01T12:00:00.000+00:00",
        expected_state="2026-01-01T12:00:00.000+00:00",
    ),
    test.case(
        "restored_unavailable",
        restored_value=STATE_UNAVAILABLE,
        expected_state=STATE_UNKNOWN,
    ),
)
async def infrared_entity_state_restore(
    restored_value: str,
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_infrared_entity: MockInfraredEntity = Depends(mock_infrared_entity_fixture),
) -> None:
    """Test infrared entity state restore."""
    mock_restore_cache(hass, [State("infrared.test_ir_transmitter", restored_value)])

    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()

    component = hass.data[DATA_COMPONENT]
    await component.async_add_entities([mock_infrared_entity])

    state = hass.states.get("infrared.test_ir_transmitter")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(expected_state)
