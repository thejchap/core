"""The tests for the Sun helpers."""

from datetime import datetime, timedelta

from astral import LocationInfo
import astral.sun
from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from homeassistant.core import HomeAssistant
from homeassistant.helpers import sun
from homeassistant.util import dt as dt_util

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def next_events(hass: HomeAssistant = Depends(hass)) -> None:
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)

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
            location.observer, utc_today + timedelta(days=mod)
        )
        if next_setting > utc_now:
            break
        mod += 1

    with freeze_time(utc_now):
        expect(sun.get_astral_event_next(hass, "dawn")).to_equal(next_dawn)
        expect(sun.get_astral_event_next(hass, "dusk")).to_equal(next_dusk)
        expect(sun.get_astral_event_next(hass, "midnight")).to_equal(next_midnight)
        expect(sun.get_astral_event_next(hass, "noon")).to_equal(next_noon)
        expect(sun.get_astral_event_next(hass, SUN_EVENT_SUNRISE)).to_equal(
            next_rising
        )
        expect(sun.get_astral_event_next(hass, SUN_EVENT_SUNSET)).to_equal(
            next_setting
        )


@test
async def date_events(hass: HomeAssistant = Depends(hass)) -> None:
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    dawn = astral.sun.dawn(location.observer, utc_today)
    dusk = astral.sun.dusk(location.observer, utc_today)
    midnight = astral.sun.midnight(location.observer, utc_today)
    noon = astral.sun.noon(location.observer, utc_today)
    sunrise = astral.sun.sunrise(location.observer, utc_today)
    sunset = astral.sun.sunset(location.observer, utc_today)

    expect(sun.get_astral_event_date(hass, "dawn", utc_today)).to_equal(dawn)
    expect(sun.get_astral_event_date(hass, "dusk", utc_today)).to_equal(dusk)
    expect(sun.get_astral_event_date(hass, "midnight", utc_today)).to_equal(midnight)
    expect(sun.get_astral_event_date(hass, "noon", utc_today)).to_equal(noon)
    expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNRISE, utc_today)).to_equal(
        sunrise
    )
    expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNSET, utc_today)).to_equal(
        sunset
    )


@test
async def date_events_default_date(hass: HomeAssistant = Depends(hass)) -> None:
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    dawn = astral.sun.dawn(location.observer, date=utc_today)
    dusk = astral.sun.dusk(location.observer, date=utc_today)
    midnight = astral.sun.midnight(location.observer, date=utc_today)
    noon = astral.sun.noon(location.observer, date=utc_today)
    sunrise = astral.sun.sunrise(location.observer, date=utc_today)
    sunset = astral.sun.sunset(location.observer, date=utc_today)

    with freeze_time(utc_now):
        expect(sun.get_astral_event_date(hass, "dawn", utc_today)).to_equal(dawn)
        expect(sun.get_astral_event_date(hass, "dusk", utc_today)).to_equal(dusk)
        expect(sun.get_astral_event_date(hass, "midnight", utc_today)).to_equal(
            midnight
        )
        expect(sun.get_astral_event_date(hass, "noon", utc_today)).to_equal(noon)
        expect(
            sun.get_astral_event_date(hass, SUN_EVENT_SUNRISE, utc_today)
        ).to_equal(sunrise)
        expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNSET, utc_today)).to_equal(
            sunset
        )


@test
async def date_events_accepts_datetime(hass: HomeAssistant = Depends(hass)) -> None:
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 8, 0, 0, tzinfo=dt_util.UTC)

    utc_today = utc_now.date()

    location = LocationInfo(
        latitude=hass.config.latitude, longitude=hass.config.longitude
    )

    dawn = astral.sun.dawn(location.observer, date=utc_today)
    dusk = astral.sun.dusk(location.observer, date=utc_today)
    midnight = astral.sun.midnight(location.observer, date=utc_today)
    noon = astral.sun.noon(location.observer, date=utc_today)
    sunrise = astral.sun.sunrise(location.observer, date=utc_today)
    sunset = astral.sun.sunset(location.observer, date=utc_today)

    expect(sun.get_astral_event_date(hass, "dawn", utc_now)).to_equal(dawn)
    expect(sun.get_astral_event_date(hass, "dusk", utc_now)).to_equal(dusk)
    expect(sun.get_astral_event_date(hass, "midnight", utc_now)).to_equal(midnight)
    expect(sun.get_astral_event_date(hass, "noon", utc_now)).to_equal(noon)
    expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNRISE, utc_now)).to_equal(
        sunrise
    )
    expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNSET, utc_now)).to_equal(sunset)


@test
async def is_up(hass: HomeAssistant = Depends(hass)) -> None:
    """Test retrieving next sun events."""
    utc_now = datetime(2016, 11, 1, 12, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(utc_now):
        expect(sun.is_up(hass)).to_be(False)

    utc_now = datetime(2016, 11, 1, 18, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(utc_now):
        expect(sun.is_up(hass)).to_be(True)


@test
async def norway_in_june(hass: HomeAssistant = Depends(hass)) -> None:
    """Test location in Norway where the sun doesn't set in summer."""
    hass.config.latitude = 69.6
    hass.config.longitude = 18.8

    june = datetime(2016, 6, 1, tzinfo=dt_util.UTC)

    expect(sun.get_astral_event_next(hass, SUN_EVENT_SUNRISE, june)).to_equal(
        datetime(2016, 7, 24, 22, 59, 45, 689645, tzinfo=dt_util.UTC)
    )
    expect(sun.get_astral_event_next(hass, SUN_EVENT_SUNSET, june)).to_equal(
        datetime(2016, 7, 25, 22, 17, 13, 503932, tzinfo=dt_util.UTC)
    )
    expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNRISE, june)).to_be_none()
    expect(sun.get_astral_event_date(hass, SUN_EVENT_SUNSET, june)).to_be_none()


@test
async def impossible_elevation(hass: HomeAssistant = Depends(hass)) -> None:
    """Test altitude where the sun can't set."""
    hass.config.latitude = 69.6
    hass.config.longitude = 18.8
    hass.config.elevation = 10000000

    june = datetime(2016, 6, 1, tzinfo=dt_util.UTC)

    expect(lambda: sun.get_astral_event_next(hass, SUN_EVENT_SUNRISE, june)).to_raise(
        ValueError
    )
