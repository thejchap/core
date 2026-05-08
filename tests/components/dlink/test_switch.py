"""Switch tests for the D-Link Smart Plug integration."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.dlink.const import DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant

from ._fixtures import CONF_DATA, mocked_plug, mocked_plug_legacy

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def switch_state(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mocked_plug: AsyncMock = Depends(mocked_plug),
) -> None:
    """Test we get the switch status."""
    with patch(
        "homeassistant.components.dlink.SmartPlug",
        return_value=mocked_plug,
    ):
        entry = MockConfigEntry(domain=DOMAIN, data=CONF_DATA)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "switch.mock_title"
    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes["total_consumption"]).to_equal(1040.0)
    expect(state.attributes["temperature"]).to_equal(33)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    expect(hass.states.get(entity_id).state).to_equal(STATE_ON)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    expect(hass.states.get(entity_id).state).to_equal(STATE_OFF)


@test
async def switch_no_value(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mocked_plug_legacy: AsyncMock = Depends(mocked_plug_legacy),
) -> None:
    """Test we handle 'N/A' being passed by the pypi package."""
    with patch(
        "homeassistant.components.dlink.SmartPlug",
        return_value=mocked_plug_legacy,
    ):
        entry = MockConfigEntry(domain=DOMAIN, data=CONF_DATA)
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("switch.mock_title")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes["total_consumption"]).to_be(None)
    expect(state.attributes["temperature"]).to_be(None)
