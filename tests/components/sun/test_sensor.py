"""The tests for the Sun sensor platform."""

from collections.abc import Generator
from datetime import datetime, timedelta
import math
from unittest.mock import patch

from astral import LocationInfo
import astral.sun
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components import sun
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.hass_fixtures import entity_registry, freezer, hass


@fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Ensure all entities are enabled in the registry."""
    with (
        patch(
            "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
            return_value=True,
        ),
        patch(
            "homeassistant.components.device_tracker.config_entry.ScannerEntity.entity_registry_enabled_default",
            return_value=True,
        ),
    ):
        yield


def _approx_equal(actual: float, expected: float, rel: float = 0.1) -> bool:
    """Return True if actual is within rel*|expected| of expected."""
    return math.isclose(actual, expected, rel_tol=rel, abs_tol=1e-9)


@test
async def setting_rising(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    _: None = Depends(entity_registry_enabled_by_default),
) -> None:
    """Test retrieving sun setting and rising."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    freezer.move_to(utc_now)
    await async_setup_component(hass, sun.DOMAIN, {sun.DOMAIN: {}})
    await hass.async_block_till_done()

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    mod = -1
    while True:
        next_dawn = astral.sun.dawn(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_dawn > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_dusk = astral.sun.dusk(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_dusk > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_midnight = astral.sun.midnight(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_midnight > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_noon = astral.sun.noon(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_noon > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_rising = astral.sun.sunrise(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_rising > utc_now:
            break
        mod += 1

    mod = -1
    while True:
        next_setting = astral.sun.sunset(
            location.observer, date=utc_today + timedelta(days=mod)
        )
        if next_setting > utc_now:
            break
        mod += 1

    expected_solar_elevation = astral.sun.elevation(location.observer, utc_now)
    expected_solar_azimuth = astral.sun.azimuth(location.observer, utc_now)

    state1 = hass.states.get("sensor.sun_next_dawn")
    state2 = hass.states.get("sensor.sun_next_dusk")
    state3 = hass.states.get("sensor.sun_next_midnight")
    state4 = hass.states.get("sensor.sun_next_noon")
    state5 = hass.states.get("sensor.sun_next_rising")
    state6 = hass.states.get("sensor.sun_next_setting")
    expect(next_dawn.replace(microsecond=0)).to_equal(
        dt_util.parse_datetime(state1.state)
    )
    expect(next_dusk.replace(microsecond=0)).to_equal(
        dt_util.parse_datetime(state2.state)
    )
    expect(next_midnight.replace(microsecond=0)).to_equal(
        dt_util.parse_datetime(state3.state)
    )
    expect(next_noon.replace(microsecond=0)).to_equal(
        dt_util.parse_datetime(state4.state)
    )
    expect(next_rising.replace(microsecond=0)).to_equal(
        dt_util.parse_datetime(state5.state)
    )
    expect(next_setting.replace(microsecond=0)).to_equal(
        dt_util.parse_datetime(state6.state)
    )
    solar_elevation_state = hass.states.get("sensor.sun_solar_elevation")
    expect(
        _approx_equal(float(solar_elevation_state.state), expected_solar_elevation)
    ).to_be(True)
    solar_azimuth_state = hass.states.get("sensor.sun_solar_azimuth")
    expect(
        _approx_equal(float(solar_azimuth_state.state), expected_solar_azimuth)
    ).to_be(True)

    entry_ids = hass.config_entries.async_entries("sun")

    entity = entity_registry.async_get("sensor.sun_next_dawn")

    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-next_dawn")

    freezer.tick(timedelta(hours=24))
    # Block once for Sun to update
    await hass.async_block_till_done()
    # Block another time for the sensors to update
    await hass.async_block_till_done()

    # Make sure all the signals work
    expect(state1.state != hass.states.get("sensor.sun_next_dawn").state).to_be(True)
    expect(state2.state != hass.states.get("sensor.sun_next_dusk").state).to_be(True)
    expect(
        state3.state != hass.states.get("sensor.sun_next_midnight").state
    ).to_be(True)
    expect(state4.state != hass.states.get("sensor.sun_next_noon").state).to_be(True)
    expect(
        state5.state != hass.states.get("sensor.sun_next_rising").state
    ).to_be(True)
    expect(
        state6.state != hass.states.get("sensor.sun_next_setting").state
    ).to_be(True)
    expect(
        solar_elevation_state.state
        != hass.states.get("sensor.sun_solar_elevation").state
    ).to_be(True)
    expect(
        solar_azimuth_state.state
        != hass.states.get("sensor.sun_solar_azimuth").state
    ).to_be(True)

    entity = entity_registry.async_get("sensor.sun_next_dusk")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-next_dusk")

    entity = entity_registry.async_get("sensor.sun_next_midnight")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-next_midnight")

    entity = entity_registry.async_get("sensor.sun_next_noon")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-next_noon")

    entity = entity_registry.async_get("sensor.sun_next_rising")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-next_rising")

    entity = entity_registry.async_get("sensor.sun_next_setting")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-next_setting")

    entity = entity_registry.async_get("sensor.sun_solar_elevation")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-solar_elevation")

    entity = entity_registry.async_get("sensor.sun_solar_azimuth")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-solar_azimuth")
