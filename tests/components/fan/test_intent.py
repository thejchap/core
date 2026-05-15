"""Intent tests for the fan platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    DOMAIN,
    SERVICE_TURN_ON,
    intent as fan_intent,
)
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

from tests.common import async_mock_service
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def set_speed_intent(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test set speed intent for fans."""
    await fan_intent.async_setup_intents(hass)

    entity_id = f"{DOMAIN}.test_fan"
    hass.states.async_set(entity_id, STATE_OFF)
    calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)

    response = await intent.async_handle(
        hass,
        "test",
        fan_intent.INTENT_FAN_SET_SPEED,
        {"name": {"value": "test fan"}, ATTR_PERCENTAGE: {"value": 50}},
    )
    await hass.async_block_till_done()

    expect(response.response_type).to_equal(intent.IntentResponseType.ACTION_DONE)
    expect(len(calls)).to_equal(1)
    call = calls[0]
    expect(call.domain).to_equal(DOMAIN)
    expect(call.service).to_equal(SERVICE_TURN_ON)
    expect(call.data).to_equal({"entity_id": entity_id, "percentage": 50})
