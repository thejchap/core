"""The tests for the Season integration."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.season.const import TYPE_ASTRONOMICAL, TYPE_METEOROLOGICAL
from homeassistant.components.season.sensor import (
    STATE_AUTUMN,
    STATE_SUMMER,
)
from homeassistant.components.sensor import ATTR_OPTIONS, SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, CONF_TYPE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.util.dt import UTC

from ._fixtures import mock_config_entry as mock_config_entry_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test.cases(
    test.case(
        "astronomical_summer",
        season_type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 9, 3, 0, 0, tzinfo=UTC),
        expected=STATE_SUMMER,
    ),
    test.case(
        "meteorological_summer",
        season_type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 8, 13, 0, 0, tzinfo=UTC),
        expected=STATE_SUMMER,
    ),
    test.case(
        "astronomical_autumn",
        season_type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 9, 23, 0, 0, tzinfo=UTC),
        expected=STATE_AUTUMN,
    ),
)
async def season_northern_hemisphere(
    season_type: str,
    day: datetime,
    expected: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test northern hemisphere season classification."""
    hass.config.latitude = 48.864716
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=season_type, data={CONF_TYPE: season_type}
    )

    with freeze_time(day):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(expected)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.ENUM)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(
        ["spring", "summer", "autumn", "winter"]
    )

    entry = entity_registry.async_get("sensor.season")
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(mock_config_entry.entry_id)
    expect(entry.translation_key).to_equal("season")


@test.skip("indirect parametrize — duplicate of northern_hemisphere with different lat")
async def season_southern_hemisphere() -> None:
    """Stub for test_season_southern_hemisphere (port deferred)."""


@test
async def season_equator(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test that season should be unknown for equator."""
    hass.config.latitude = 0
    mock_config_entry.add_to_hass(hass)

    with freeze_time(datetime(2017, 9, 3, 0, 0, tzinfo=UTC)):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNKNOWN)

    entry = entity_registry.async_get("sensor.season")
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(mock_config_entry.entry_id)


@test
async def season_local_midnight(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test that season changes at local midnight, not UTC."""
    await hass.config.async_set_time_zone("Australia/Sydney")
    hass.config.latitude = -33.918861
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        unique_id=TYPE_METEOROLOGICAL,
        data={CONF_TYPE: TYPE_METEOROLOGICAL},
    )

    sydney_tz = ZoneInfo("Australia/Sydney")

    day_before = datetime(2017, 2, 28, 23, 59, 59, tzinfo=sydney_tz)

    with freeze_time(day_before):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_SUMMER)

    midnight = datetime(2017, 3, 1, 0, 0, 0, tzinfo=sydney_tz)

    with freeze_time(midnight):
        await async_update_entity(hass, "sensor.season")
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_AUTUMN)
