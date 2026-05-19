"""Tryke fixtures for the calendar tests."""

from __future__ import annotations

from collections.abc import Generator
import datetime
import secrets
from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, fixture

from homeassistant.components.calendar import (
    DOMAIN,
    CalendarEntity,
    CalendarEntityDescription,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from tests.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock

TEST_DOMAIN = "test"


class _MockFlow(ConfigFlow):
    """Test flow."""


class MockCalendarEntity(CalendarEntity):
    """Test Calendar entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        name: str,
        events: list[CalendarEvent] | None = None,
        initial_color: str | None = None,
        unique_id: str | None = None,
    ) -> None:
        """Initialize entity."""
        self._attr_name = name.capitalize()
        self._events = events or []
        self._attr_unique_id = unique_id
        self.entity_description = CalendarEntityDescription(
            key=unique_id or name,
            initial_color=initial_color,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return self._events[0] if self._events else None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        assert start_date < end_date
        events = []
        for event in self._events:
            if event.start_datetime_local >= end_date:
                continue
            if event.end_datetime_local < start_date:
                continue
            events.append(event)
        return events


def _create_test_entities() -> list[MockCalendarEntity]:
    """Create test entities used during the test."""
    half_hour_from_now = dt_util.now() + datetime.timedelta(minutes=30)
    entity1 = MockCalendarEntity(
        "Calendar 1",
        [
            CalendarEvent(
                start=half_hour_from_now,
                end=half_hour_from_now + datetime.timedelta(minutes=60),
                summary="Future Event",
                description="Future Description",
                location="Future Location",
                uid="calendar-event-uid-1",
                rrule="FREQ=WEEKLY;COUNT=3",
                recurrence_id="20260415",
            )
        ],
        unique_id="calendar_1_id",
    )
    entity1.async_get_events = AsyncMock(wraps=entity1.async_get_events)

    middle_of_event = dt_util.now() - datetime.timedelta(minutes=30)
    entity2 = MockCalendarEntity(
        "Calendar 2",
        [
            CalendarEvent(
                start=middle_of_event,
                end=middle_of_event + datetime.timedelta(minutes=60),
                summary="Current Event",
            )
        ],
        unique_id="calendar_2_id",
    )
    entity2.async_get_events = AsyncMock(wraps=entity2.async_get_events)

    entity3 = MockCalendarEntity(
        "Calendar 3", [], initial_color="#FF0000", unique_id="calendar_3"
    )
    entity3.async_get_events = AsyncMock(wraps=entity3.async_get_events)

    return [entity1, entity2, entity3]


@fixture
async def set_time_zone(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set the time zone for the tests."""
    # America/Regina stays UTC-6 year round, useful for stable calculations.
    await hass.config.async_set_time_zone("America/Regina")


@fixture
def config_flow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    with mock_config_flow(TEST_DOMAIN, _MockFlow):
        yield


@fixture
async def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Create a mock config entry."""
    entry = MockConfigEntry(domain=TEST_DOMAIN)
    entry.add_to_hass(hass)
    return entry


@fixture
def test_entities() -> list[MockCalendarEntity]:
    """List that holds the fake entities created during the test."""
    return []


@fixture
def mock_setup_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture),
    test_entities: list[MockCalendarEntity] = Depends(test_entities),
) -> None:
    """Set up a mock integration providing the calendar platform."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.CALENDAR]
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> bool:
        await hass.config_entries.async_unload_platforms(
            config_entry, [Platform.CALENDAR]
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
            async_unload_entry=async_unload_entry_init,
        ),
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test calendar platform via config entry."""
        new_entities = _create_test_entities()
        test_entities.clear()
        test_entities.extend(new_entities)
        async_add_entities(test_entities)

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Any:
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)
