"""The tests for the date component."""

from datetime import date

from tryke import Depends, expect, fixture, test

from homeassistant.components.date import DOMAIN, SERVICE_SET_VALUE
from homeassistant.const import (
    ATTR_DATE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    CONF_PLATFORM,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import MockDateEntity

from tests.common import setup_test_component_platform
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def date_entity(hass: HomeAssistant = Depends(hass)) -> None:
    """Test date entity."""
    entity = MockDateEntity(
        name="test",
        unique_id="unique_date",
        native_value=date(2020, 1, 1),
    )
    setup_test_component_platform(hass, DOMAIN, [entity])

    result = await async_setup_component(
        hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}}
    )
    expect(result).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("date.test")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("2020-01-01")
    expect(state.attributes).to_equal({ATTR_FRIENDLY_NAME: "test"})

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_DATE: date(2021, 1, 1), ATTR_ENTITY_ID: "date.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("date.test")
    expect(state.state).to_equal("2021-01-01")

    date_entity = MockDateEntity(native_value=None)
    expect(date_entity.state is None).to_be(True)
    expect(date_entity.state_attributes is None).to_be(True)
