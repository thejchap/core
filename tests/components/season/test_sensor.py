"""The tests for the Season integration."""

from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.season.const import (
    DOMAIN,
    TYPE_ASTRONOMICAL,
    TYPE_METEOROLOGICAL,
)
from homeassistant.components.season.sensor import (
    STATE_AUTUMN,
    STATE_SPRING,
    STATE_SUMMER,
    STATE_WINTER,
)
from homeassistant.components.sensor import ATTR_OPTIONS, SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, CONF_TYPE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.util.dt import UTC

from tests.common import MockConfigEntry
from tests.components.season._fixtures import mock_config_entry
from tests.hass_fixtures import device_registry, entity_registry, hass

HEMISPHERE_NORTHERN = {
    "homeassistant": {"latitude": 48.864716, "longitude": 2.349014},
    "sensor": {"platform": "season", "type": "astronomical"},
}

HEMISPHERE_SOUTHERN = {
    "homeassistant": {"latitude": -33.918861, "longitude": 18.423300},
    "sensor": {"platform": "season", "type": "astronomical"},
}

HEMISPHERE_EQUATOR = {
    "homeassistant": {"latitude": 0, "longitude": -51.065100},
    "sensor": {"platform": "season", "type": "astronomical"},
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "astronomical_20170903_summer",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 9, 3, 0, 0, tzinfo=UTC),
        expected=STATE_SUMMER,
    ),
    test.case(
        "meteorological_20170813_summer",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 8, 13, 0, 0, tzinfo=UTC),
        expected=STATE_SUMMER,
    ),
    test.case(
        "astronomical_20170923_autumn",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 9, 23, 0, 0, tzinfo=UTC),
        expected=STATE_AUTUMN,
    ),
    test.case(
        "meteorological_20170903_autumn",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 9, 3, 0, 0, tzinfo=UTC),
        expected=STATE_AUTUMN,
    ),
    test.case(
        "astronomical_20171225_winter",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 12, 25, 0, 0, tzinfo=UTC),
        expected=STATE_WINTER,
    ),
    test.case(
        "meteorological_20171203_winter",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 12, 3, 0, 0, tzinfo=UTC),
        expected=STATE_WINTER,
    ),
    test.case(
        "astronomical_20170401_spring",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 4, 1, 0, 0, tzinfo=UTC),
        expected=STATE_SPRING,
    ),
    test.case(
        "meteorological_20170303_spring",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 3, 3, 0, 0, tzinfo=UTC),
        expected=STATE_SPRING,
    ),
)
async def season_northern_hemisphere(
    type: str,
    day: datetime,
    expected: str,
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that season should be summer."""
    hass.config.latitude = HEMISPHERE_NORTHERN["homeassistant"]["latitude"]
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=type, data={CONF_TYPE: type}
    )

    with freeze_time(day):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(expected)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.ENUM)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(
        ["spring", "summer", "autumn", "winter"]
    )

    entry = entity_registry.async_get("sensor.season")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal(mock_config_entry.entry_id)
    expect(entry.translation_key).to_equal("season")


@test.cases(
    test.case(
        "astronomical_20171225_summer",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 12, 25, 0, 0, tzinfo=UTC),
        expected=STATE_SUMMER,
    ),
    test.case(
        "meteorological_20171203_summer",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 12, 3, 0, 0, tzinfo=UTC),
        expected=STATE_SUMMER,
    ),
    test.case(
        "astronomical_20170401_autumn",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 4, 1, 0, 0, tzinfo=UTC),
        expected=STATE_AUTUMN,
    ),
    test.case(
        "meteorological_20170303_autumn",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 3, 3, 0, 0, tzinfo=UTC),
        expected=STATE_AUTUMN,
    ),
    test.case(
        "astronomical_20170903_winter",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 9, 3, 0, 0, tzinfo=UTC),
        expected=STATE_WINTER,
    ),
    test.case(
        "meteorological_20170813_winter",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 8, 13, 0, 0, tzinfo=UTC),
        expected=STATE_WINTER,
    ),
    test.case(
        "astronomical_20170923_spring",
        type=TYPE_ASTRONOMICAL,
        day=datetime(2017, 9, 23, 0, 0, tzinfo=UTC),
        expected=STATE_SPRING,
    ),
    test.case(
        "meteorological_20170903_spring",
        type=TYPE_METEOROLOGICAL,
        day=datetime(2017, 9, 3, 0, 0, tzinfo=UTC),
        expected=STATE_SPRING,
    ),
)
async def season_southern_hemisphere(
    type: str,
    day: datetime,
    expected: str,
    hass: HomeAssistant = Depends(hass),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that season should be summer."""
    hass.config.latitude = HEMISPHERE_SOUTHERN["homeassistant"]["latitude"]
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, unique_id=type, data={CONF_TYPE: type}
    )

    with freeze_time(day):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(expected)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.ENUM)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(
        ["spring", "summer", "autumn", "winter"]
    )

    entry = entity_registry.async_get("sensor.season")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal(mock_config_entry.entry_id)
    expect(entry.translation_key).to_equal("season")

    expect(bool(entry.device_id)).to_be(True)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry is not None).to_be(True)
    expect(device_entry.identifiers).to_equal(
        {(DOMAIN, mock_config_entry.entry_id)}
    )
    expect(device_entry.entry_type).to_equal(dr.DeviceEntryType.SERVICE)


@test
async def season_equator(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that season should be unknown for equator."""
    hass.config.latitude = HEMISPHERE_EQUATOR["homeassistant"]["latitude"]
    mock_config_entry.add_to_hass(hass)

    with freeze_time(datetime(2017, 9, 3, 0, 0, tzinfo=UTC)):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    entry = entity_registry.async_get("sensor.season")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal(mock_config_entry.entry_id)


@test
async def season_local_midnight(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that season changes at local midnight, not UTC."""
    await hass.config.async_set_time_zone("Australia/Sydney")
    hass.config.latitude = HEMISPHERE_SOUTHERN["homeassistant"]["latitude"]
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        unique_id=TYPE_METEOROLOGICAL,
        data={CONF_TYPE: TYPE_METEOROLOGICAL},
    )

    sydney_tz = ZoneInfo("Australia/Sydney")

    # The day before autumn starts, at 23:59:59 local time (summer)
    day_before = datetime(2017, 2, 28, 23, 59, 59, tzinfo=sydney_tz)

    with freeze_time(day_before):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_SUMMER)

    # Exactly midnight local time (autumn)
    midnight = datetime(2017, 3, 1, 0, 0, 0, tzinfo=sydney_tz)

    with freeze_time(midnight):
        await async_update_entity(hass, "sensor.season")
        await hass.async_block_till_done()

    state = hass.states.get("sensor.season")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_AUTUMN)
