"""The tests for the Islamic prayer times sensor platform."""

from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.islamic_prayer_times.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import NOW, PRAYER_TIMES, PRAYER_TIMES_TOMORROW, PRAYER_TIMES_YESTERDAY

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


_FAKE_TRANSLATIONS = {
    "component.islamic_prayer_times.entity.sensor.fajr.name": "Fajr prayer",
    "component.islamic_prayer_times.entity.sensor.sunrise.name": "Sunrise time",
    "component.islamic_prayer_times.entity.sensor.dhuhr.name": "Dhuhr prayer",
    "component.islamic_prayer_times.entity.sensor.asr.name": "Asr prayer",
    "component.islamic_prayer_times.entity.sensor.maghrib.name": "Maghrib prayer",
    "component.islamic_prayer_times.entity.sensor.isha.name": "Isha prayer",
    "component.islamic_prayer_times.entity.sensor.midnight.name": "Midnight time",
}


async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor: set timezone to UTC for all tests."""
    await hass.config.async_set_time_zone("UTC")
    return hass


@test.cases(
    # Fajr
    test.case("fajr_yesterday", key="Fajr", sensor_name="sensor.islamic_prayer_times_fajr_prayer", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("fajr_yesterday_44", key="Fajr", sensor_name="sensor.islamic_prayer_times_fajr_prayer", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("fajr_today_44_01", key="Fajr", sensor_name="sensor.islamic_prayer_times_fajr_prayer", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("fajr_today_45", key="Fajr", sensor_name="sensor.islamic_prayer_times_fajr_prayer", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("fajr_tomorrow_45_01", key="Fajr", sensor_name="sensor.islamic_prayer_times_fajr_prayer", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
    # Sunrise
    test.case("sunrise_yesterday", key="Sunrise", sensor_name="sensor.islamic_prayer_times_sunrise_time", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("sunrise_yesterday_44", key="Sunrise", sensor_name="sensor.islamic_prayer_times_sunrise_time", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("sunrise_today_44_01", key="Sunrise", sensor_name="sensor.islamic_prayer_times_sunrise_time", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("sunrise_today_45", key="Sunrise", sensor_name="sensor.islamic_prayer_times_sunrise_time", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("sunrise_tomorrow_45_01", key="Sunrise", sensor_name="sensor.islamic_prayer_times_sunrise_time", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
    # Dhuhr
    test.case("dhuhr_yesterday", key="Dhuhr", sensor_name="sensor.islamic_prayer_times_dhuhr_prayer", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("dhuhr_yesterday_44", key="Dhuhr", sensor_name="sensor.islamic_prayer_times_dhuhr_prayer", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("dhuhr_today_44_01", key="Dhuhr", sensor_name="sensor.islamic_prayer_times_dhuhr_prayer", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("dhuhr_today_45", key="Dhuhr", sensor_name="sensor.islamic_prayer_times_dhuhr_prayer", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("dhuhr_tomorrow_45_01", key="Dhuhr", sensor_name="sensor.islamic_prayer_times_dhuhr_prayer", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
    # Asr
    test.case("asr_yesterday", key="Asr", sensor_name="sensor.islamic_prayer_times_asr_prayer", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("asr_yesterday_44", key="Asr", sensor_name="sensor.islamic_prayer_times_asr_prayer", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("asr_today_44_01", key="Asr", sensor_name="sensor.islamic_prayer_times_asr_prayer", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("asr_today_45", key="Asr", sensor_name="sensor.islamic_prayer_times_asr_prayer", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("asr_tomorrow_45_01", key="Asr", sensor_name="sensor.islamic_prayer_times_asr_prayer", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
    # Maghrib
    test.case("maghrib_yesterday", key="Maghrib", sensor_name="sensor.islamic_prayer_times_maghrib_prayer", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("maghrib_yesterday_44", key="Maghrib", sensor_name="sensor.islamic_prayer_times_maghrib_prayer", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("maghrib_today_44_01", key="Maghrib", sensor_name="sensor.islamic_prayer_times_maghrib_prayer", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("maghrib_today_45", key="Maghrib", sensor_name="sensor.islamic_prayer_times_maghrib_prayer", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("maghrib_tomorrow_45_01", key="Maghrib", sensor_name="sensor.islamic_prayer_times_maghrib_prayer", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
    # Isha
    test.case("isha_yesterday", key="Isha", sensor_name="sensor.islamic_prayer_times_isha_prayer", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("isha_yesterday_44", key="Isha", sensor_name="sensor.islamic_prayer_times_isha_prayer", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("isha_today_44_01", key="Isha", sensor_name="sensor.islamic_prayer_times_isha_prayer", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("isha_today_45", key="Isha", sensor_name="sensor.islamic_prayer_times_isha_prayer", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("isha_tomorrow_45_01", key="Isha", sensor_name="sensor.islamic_prayer_times_isha_prayer", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
    # Midnight
    test.case("midnight_yesterday", key="Midnight", sensor_name="sensor.islamic_prayer_times_midnight_time", offset=timedelta(days=-1), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("midnight_yesterday_44", key="Midnight", sensor_name="sensor.islamic_prayer_times_midnight_time", offset=timedelta(minutes=44), prayer_times=PRAYER_TIMES_YESTERDAY),
    test.case("midnight_today_44_01", key="Midnight", sensor_name="sensor.islamic_prayer_times_midnight_time", offset=timedelta(minutes=44, seconds=1), prayer_times=PRAYER_TIMES),
    test.case("midnight_today_45", key="Midnight", sensor_name="sensor.islamic_prayer_times_midnight_time", offset=timedelta(days=1, minutes=45), prayer_times=PRAYER_TIMES),
    test.case("midnight_tomorrow_45_01", key="Midnight", sensor_name="sensor.islamic_prayer_times_midnight_time", offset=timedelta(days=1, minutes=45, seconds=1), prayer_times=PRAYER_TIMES_TOMORROW),
)
async def islamic_prayer_times_sensors(
    *,
    key: str,
    sensor_name: str,
    offset: timedelta,
    prayer_times: dict[str, str],
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test minimum Islamic prayer times configuration."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    with (
        patch(
            "prayer_times_calculator_offline.PrayerTimesCalculator.fetch_prayer_times",
            side_effect=(PRAYER_TIMES_YESTERDAY, PRAYER_TIMES, PRAYER_TIMES_TOMORROW),
        ),
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
        freeze_time(NOW + offset),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        state = hass.states.get(sensor_name)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(prayer_times[key])
