"""Tests for Islamic Prayer Times init."""

from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.islamic_prayer_times.const import CONF_CALC_METHOD, DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from . import NOW, PRAYER_TIMES

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    await hass.config.async_set_time_zone("UTC")
    return hass


@test
async def successful_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that Islamic Prayer Times is configured successfully."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with patch(
        "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
        return_value=PRAYER_TIMES,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test removing Islamic Prayer Times."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with patch(
        "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
        return_value=PRAYER_TIMES,
    ):
        await hass.config_entries.async_setup(entry.entry_id)

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def options_listener(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Ensure updating options triggers a coordinator refresh."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with (
        patch(
            "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
            return_value=PRAYER_TIMES,
        ) as mock_fetch_prayer_times,
        freeze_time(NOW),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_fetch_prayer_times.call_count).to_equal(3)
        mock_fetch_prayer_times.reset_mock()

        hass.config_entries.async_update_entry(
            entry, options={CONF_CALC_METHOD: "makkah"}
        )
        await hass.async_block_till_done()
        expect(mock_fetch_prayer_times.call_count).to_equal(3)


@test.cases(
    test.case("fajr", object_id="fajer_prayer", old_unique_id="Fajr"),
    test.case("dhuhr", object_id="dhuhr_prayer", old_unique_id="Dhuhr"),
)
async def migrate_unique_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    *,
    object_id: str,
    old_unique_id: str,
) -> None:
    """Test unique id migration."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get_or_create(
        suggested_object_id=object_id,
        domain=SENSOR_DOMAIN,
        platform=DOMAIN,
        unique_id=old_unique_id,
        config_entry=entry,
    )
    expect(entity.unique_id).to_equal(old_unique_id)

    with (
        patch(
            "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
            return_value=PRAYER_TIMES,
        ),
        freeze_time(NOW),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_migrated = entity_registry.async_get(entity.entity_id)
    assert entity_migrated is not None
    expect(entity_migrated.unique_id).to_equal(f"{entry.entry_id}-{old_unique_id}")


@test
async def migration_from_1_1_to_1_2(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test migrating from version 1.1 to 1.2."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with (
        patch(
            "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
            return_value=PRAYER_TIMES,
        ),
        freeze_time(NOW),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.data).to_equal(
        {
            CONF_LATITUDE: hass.config.latitude,
            CONF_LONGITUDE: hass.config.longitude,
        }
    )
    expect(entry.minor_version).to_equal(2)


@test
async def update_scheduling(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that integration schedules update immediately after Islamic midnight."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with (
        patch(
            "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
            return_value=PRAYER_TIMES,
        ),
        freeze_time(NOW),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.LOADED)

    with patch(
        "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
        return_value=PRAYER_TIMES,
    ) as mock_fetch_prayer_times:
        midnight_time = dt_util.parse_datetime(PRAYER_TIMES["Midnight"])
        assert midnight_time is not None
        with freeze_time(midnight_time):
            async_fire_time_changed(hass, midnight_time)
            await hass.async_block_till_done()
            mock_fetch_prayer_times.assert_not_called()

        midnight_time += timedelta(seconds=1)
        with freeze_time(midnight_time):
            async_fire_time_changed(hass, midnight_time)
            await hass.async_block_till_done()
            expect(mock_fetch_prayer_times.call_count).to_equal(3)
