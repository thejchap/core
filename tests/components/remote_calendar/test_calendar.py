"""Tests for calendar platform of Remote Calendar."""

import textwrap

from httpx import Response
from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, set_time_zone

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import respx_mock_session

CALENDER_URL = "https://some.calendar.com/calendar.ics"
TEST_ENTITY = "calendar.home_assistant_events"
FRIENDLY_NAME = "Home Assistant Events"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _tz: None = Depends(set_time_zone),
) -> None:
    """Force tryke to fully resolve hass + time zone before each test."""


@test
async def empty_calendar(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that an empty calendar is set up and reports STATE_OFF."""
    async with respx_mock_session() as respx_mock:
        respx_mock.get(CALENDER_URL).mock(
            return_value=Response(
                status_code=200,
                text=textwrap.dedent(
                    """BEGIN:VCALENDAR
                    VERSION:2.0
                    PRODID:-//hacksw/handcal//NONSGML v1.0//EN
                    END:VCALENDAR
                """
                ),
            )
        )
        await setup_integration(hass, config_entry)

        state = hass.states.get(TEST_ENTITY)
        expect(state is not None).to_be(True)
        expect(state.name).to_equal(FRIENDLY_NAME)
        expect(state.state).to_equal(STATE_OFF)


@test.skip("indirect parametrize - port deferred")
async def api_date_time_event() -> None:
    """Stub for test_api_date_time_event (port deferred)."""

@test.skip("indirect parametrize - port deferred")
async def api_date_event() -> None:
    """Stub for test_api_date_event (port deferred)."""

@test.skip("requires freezegun + recurrence handling - port deferred")
async def active_event() -> None:
    """Stub for test_active_event (port deferred)."""

@test.skip("requires freezegun + recurrence handling - port deferred")
async def upcoming_event() -> None:
    """Stub for test_upcoming_event (port deferred)."""

@test.skip("requires freezegun + recurrence handling - port deferred")
async def recurring_event() -> None:
    """Stub for test_recurring_event (port deferred)."""

@test.skip("requires syrupy snapshots for full event response")
async def all_day_iter_order() -> None:
    """Stub for test_all_day_iter_order (port deferred)."""

@test.skip("indirect parametrize across .ics testdata files - port deferred")
async def calendar_examples() -> None:
    """Stub for test_calendar_examples (port deferred)."""

@test.skip("requires freezegun event lifecycle - port deferred")
async def event_lifecycle() -> None:
    """Stub for test_event_lifecycle (port deferred)."""

@test.skip("requires freezegun edge timing - port deferred")
async def event_edge_during_refresh_interval() -> None:
    """Stub for test_event_edge_during_refresh_interval (port deferred)."""
