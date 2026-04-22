"""The tests for the Sun binary_sensor platform."""

from collections.abc import Generator
from datetime import datetime, timedelta
from unittest.mock import patch

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

    expect(hass.states.get("binary_sensor.sun_solar_rising").state).to_equal("on")

    entry_ids = hass.config_entries.async_entries("sun")

    freezer.tick(timedelta(hours=12))
    # Block once for Sun to update
    await hass.async_block_till_done()
    # Block another time for the sensors to update
    await hass.async_block_till_done()

    # Make sure all the signals work
    expect(hass.states.get("binary_sensor.sun_solar_rising").state).to_equal("off")

    entity = entity_registry.async_get("binary_sensor.sun_solar_rising")
    expect(entity is not None).to_be(True)
    expect(entity.entity_category).to_be(EntityCategory.DIAGNOSTIC)
    expect(entity.unique_id).to_equal(f"{entry_ids[0].entry_id}-solar_rising")
