"""Tryke fixtures for the remote_calendar integration."""

import textwrap

from tryke import Depends, fixture

from homeassistant.components.remote_calendar.const import CONF_CALENDAR_NAME, DOMAIN
from homeassistant.const import CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx

CALENDAR_NAME = "Home Assistant Events"
CALENDER_URL = "https://some.calendar.com/calendar.ics"


@fixture
def time_zone() -> str:
    """Fixture for time zone to use in tests."""
    return "America/Regina"


@fixture
async def set_time_zone(
    hass: HomeAssistant = Depends(hass_fx),
    time_zone: str = Depends(time_zone),
) -> None:
    """Set the time zone for the tests."""
    await hass.config.async_set_time_zone(time_zone)


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Fixture for mock configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CALENDAR_NAME: CALENDAR_NAME,
            CONF_URL: CALENDER_URL,
            CONF_VERIFY_SSL: True,
        },
    )


@fixture
def ics_content() -> str:
    """Fixture to allow tests to set initial ics content for the calendar store."""
    return textwrap.dedent(
        """\
        BEGIN:VCALENDAR
        BEGIN:VEVENT
        SUMMARY:Bastille Day Party
        DTSTART:19970714T170000Z
        DTEND:19970715T040000Z
        END:VEVENT
        END:VCALENDAR
        """
    )
