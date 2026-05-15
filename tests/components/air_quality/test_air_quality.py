"""The tests for the Air Quality component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.air_quality import ATTR_N2O, ATTR_OZONE, ATTR_PM_10
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    await async_setup_component(hass, "homeassistant", {})
    return hass


@test
async def state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test Air Quality state."""
    config = {"air_quality": {"platform": "demo"}}

    expect(await async_setup_component(hass, "air_quality", config)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("air_quality.demo_air_quality_home")
    expect(state is not None).to_be(True)

    expect(state.state).to_equal("14")


@test
async def attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test Air Quality attributes."""
    config = {"air_quality": {"platform": "demo"}}

    expect(await async_setup_component(hass, "air_quality", config)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("air_quality.demo_air_quality_office")
    expect(state is not None).to_be(True)

    data = state.attributes
    expect(data.get(ATTR_PM_10)).to_equal(16)
    expect(data.get(ATTR_N2O)).to_be(None)
    expect(data.get(ATTR_OZONE)).to_be(None)
    expect(data.get(ATTR_ATTRIBUTION)).to_equal("Powered by Home Assistant")
    expect(data.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
