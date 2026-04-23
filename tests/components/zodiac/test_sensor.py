"""The test for the zodiac sensor platform."""

from datetime import datetime
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import ATTR_OPTIONS, SensorDeviceClass
from homeassistant.components.zodiac.const import (
    ATTR_ELEMENT,
    ATTR_MODALITY,
    DOMAIN,
    ELEMENT_EARTH,
    ELEMENT_FIRE,
    ELEMENT_WATER,
    MODALITY_CARDINAL,
    MODALITY_FIXED,
    SIGN_ARIES,
    SIGN_SCORPIO,
    SIGN_TAURUS,
)
from homeassistant.const import ATTR_DEVICE_CLASS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass

DAY1 = datetime(2020, 11, 15, tzinfo=dt_util.UTC)
DAY2 = datetime(2020, 4, 20, tzinfo=dt_util.UTC)
DAY3 = datetime(2020, 4, 21, tzinfo=dt_util.UTC)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("scorpio", DAY1, SIGN_SCORPIO, ELEMENT_WATER, MODALITY_FIXED),
    test.case("aries", DAY2, SIGN_ARIES, ELEMENT_FIRE, MODALITY_CARDINAL),
    test.case("taurus", DAY3, SIGN_TAURUS, ELEMENT_EARTH, MODALITY_FIXED),
)
async def zodiac_day(
    now: datetime,
    sign: str,
    element: str,
    modality: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the zodiac sensor."""
    await hass.config.async_set_time_zone("UTC")
    MockConfigEntry(
        domain=DOMAIN,
    ).add_to_hass(hass)

    with patch("homeassistant.components.zodiac.sensor.utcnow", return_value=now):
        result = await async_setup_component(hass, DOMAIN, {})
        expect(result).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.zodiac")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(sign)
    expect(bool(state.attributes)).to_be(True)
    expect(state.attributes[ATTR_ELEMENT]).to_equal(element)
    expect(state.attributes[ATTR_MODALITY]).to_equal(modality)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.ENUM)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(
        [
            "aquarius",
            "aries",
            "cancer",
            "capricorn",
            "gemini",
            "leo",
            "libra",
            "pisces",
            "sagittarius",
            "scorpio",
            "taurus",
            "virgo",
        ]
    )

    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get("sensor.zodiac")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("zodiac")
    expect(entry.translation_key).to_equal("sign")
