"""The tests for the Switch component (tryke port)."""

from collections.abc import Generator

from tryke import Depends, expect, fixture, test

from homeassistant import core, loader
from homeassistant.components import switch
from homeassistant.const import CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import common
from .common import MockSwitch, get_mock_switch_entities

from tests.common import MockUser, setup_test_component_platform
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@fixture
def enable_custom_integrations(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> Generator[None]:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    yield


@fixture
def entities(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> list[MockSwitch]:
    """Initialize the test switch."""
    mock_switch_entities = get_mock_switch_entities()
    setup_test_component_platform(hass, switch.DOMAIN, mock_switch_entities)
    return mock_switch_entities


@test
async def methods(
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockSwitch] = Depends(entities),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test is_on, turn_on, turn_off methods."""
    switch_1, switch_2, switch_3 = entities
    expect(
        await async_setup_component(
            hass, switch.DOMAIN, {switch.DOMAIN: {CONF_PLATFORM: "test"}}
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(switch.is_on(hass, switch_1.entity_id)).to_be_truthy()
    expect(switch.is_on(hass, switch_2.entity_id)).to_be_falsy()
    expect(switch.is_on(hass, switch_3.entity_id)).to_be_falsy()

    await common.async_turn_off(hass, switch_1.entity_id)
    await common.async_turn_on(hass, switch_2.entity_id)

    expect(switch.is_on(hass, switch_1.entity_id)).to_be_falsy()
    expect(switch.is_on(hass, switch_2.entity_id)).to_be_truthy()

    # Turn all off
    await common.async_turn_off(hass)

    expect(switch.is_on(hass, switch_1.entity_id)).to_be_falsy()
    expect(switch.is_on(hass, switch_2.entity_id)).to_be_falsy()
    expect(switch.is_on(hass, switch_3.entity_id)).to_be_falsy()

    # Turn all on
    await common.async_turn_on(hass)

    expect(switch.is_on(hass, switch_1.entity_id)).to_be_truthy()
    expect(switch.is_on(hass, switch_2.entity_id)).to_be_truthy()
    expect(switch.is_on(hass, switch_3.entity_id)).to_be_truthy()


@test
async def switch_context(
    hass: HomeAssistant = Depends(_trigger_executor),
    entities: list[MockSwitch] = Depends(entities),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test that switch context works."""
    expect(
        await async_setup_component(hass, "switch", {"switch": {"platform": "test"}})
    ).to_be_truthy()

    await hass.async_block_till_done()

    state = hass.states.get("switch.ac")
    expect(state is not None).to_be(True)

    await hass.services.async_call(
        "switch",
        "toggle",
        {"entity_id": state.entity_id},
        True,
        core.Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("switch.ac")
    expect(state2 is not None).to_be(True)
    expect(state.state != state2.state).to_be(True)
    expect(state2.context.user_id).to_equal(hass_admin_user.id)
