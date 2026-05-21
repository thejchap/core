"""The tests for the logbook component."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import Mock

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import core as ha
from homeassistant.components import logbook, recorder

# pylint: disable-next=hass-component-root-import
from homeassistant.components.alexa.smart_home import EVENT_ALEXA_SMART_HOME
from homeassistant.components.automation import EVENT_AUTOMATION_TRIGGERED
from homeassistant.components.logbook.models import EventAsRow, LazyEventPartialState
from homeassistant.components.logbook.processor import EventProcessor
from homeassistant.components.logbook.queries.common import PSEUDO_EVENT_STATE_CHANGED
from homeassistant.components.recorder.models import ulid_to_bytes_or_none
from homeassistant.components.script import EVENT_SCRIPT_STARTED
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import (
    ATTR_DOMAIN,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
    ATTR_SERVICE,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_DOMAINS,
    CONF_ENTITIES,
    CONF_EXCLUDE,
    CONF_INCLUDE,
    EVENT_CALL_SERVICE,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    EVENT_LOGBOOK_ENTRY,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import Context, Event, HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entityfilter import CONF_ENTITY_GLOBS
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import hass_ as hass_logbook, recorder_mock, set_utc
from .common import (
    MockRow,
    assert_thermostat_context_chain_events,
    mock_humanify,
    setup_thermostat_context_test_entities,
    simulate_thermostat_context_chain,
)

from tests.common import MockConfigEntry, async_capture_events, mock_platform
from tests.components.recorder.common import (
    async_recorder_block_till_done,
    async_wait_recording_done,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    hass_client,
    hass_ws_client,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder=Depends(recorder_mock),
) -> int:
    """Tryke executor trigger for async fixtures with Depends."""
    return 0


EMPTY_CONFIG = logbook.CONFIG_SCHEMA({logbook.DOMAIN: {}})


@test
async def service_call_create_logbook_entry(
    _trigger: int = Depends(_trigger_executor),
    hass_: HomeAssistant = Depends(hass_logbook),
) -> None:
    """Test if service call create log book entry."""
    calls = async_capture_events(hass_, logbook.EVENT_LOGBOOK_ENTRY)

    await hass_.services.async_call(
        logbook.DOMAIN,
        "log",
        {
            logbook.ATTR_NAME: "Alarm",
            logbook.ATTR_MESSAGE: "is triggered",
            logbook.ATTR_DOMAIN: "switch",
            logbook.ATTR_ENTITY_ID: "switch.test_switch",
        },
        True,
    )
    await hass_.services.async_call(
        logbook.DOMAIN,
        "log",
        {
            logbook.ATTR_NAME: "This entry",
            logbook.ATTR_MESSAGE: "has no domain or entity_id",
        },
        True,
    )
    await async_wait_recording_done(hass_)
    event_processor = EventProcessor(hass_, (EVENT_LOGBOOK_ENTRY,))

    events = list(
        event_processor.get_events(
            dt_util.utcnow() - timedelta(hours=1),
            dt_util.utcnow() + timedelta(hours=1),
        )
    )
    expect(len(events)) == 2

    expect(len(calls)) == 2
    first_call = calls[-2]

    expect(first_call.data.get(logbook.ATTR_NAME)) == "Alarm"
    expect(first_call.data.get(logbook.ATTR_MESSAGE)) == "is triggered"
    expect(first_call.data.get(logbook.ATTR_DOMAIN)) == "switch"
    expect(first_call.data.get(logbook.ATTR_ENTITY_ID)) == "switch.test_switch"

    last_call = calls[-1]

    expect(last_call.data.get(logbook.ATTR_NAME)) == "This entry"
    expect(last_call.data.get(logbook.ATTR_MESSAGE)) == "has no domain or entity_id"
    expect(last_call.data.get(logbook.ATTR_DOMAIN)) == "logbook"


@test
async def service_call_create_logbook_entry_invalid_entity_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if service call create log book entry with an invalid entity id."""
    await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()
    hass.bus.async_fire(
        logbook.EVENT_LOGBOOK_ENTRY,
        {
            logbook.ATTR_NAME: "Alarm",
            logbook.ATTR_MESSAGE: "is triggered",
            logbook.ATTR_DOMAIN: "switch",
            logbook.ATTR_ENTITY_ID: 1234,
        },
    )
    await async_wait_recording_done(hass)
    event_processor = EventProcessor(hass, (EVENT_LOGBOOK_ENTRY,))
    events = list(
        event_processor.get_events(
            dt_util.utcnow() - timedelta(hours=1),
            dt_util.utcnow() + timedelta(hours=1),
        )
    )
    expect(len(events)) == 1
    expect(events[0][logbook.ATTR_DOMAIN]) == "switch"
    expect(events[0][logbook.ATTR_NAME]) == "Alarm"
    expect(events[0][logbook.ATTR_ENTITY_ID]) == 1234
    expect(events[0][logbook.ATTR_MESSAGE]) == "is triggered"


@test
async def service_call_create_log_book_entry_no_message(
    _trigger: int = Depends(_trigger_executor),
    hass_: HomeAssistant = Depends(hass_logbook),
) -> None:
    """Test if service call create log book entry without message."""
    calls = async_capture_events(hass_, logbook.EVENT_LOGBOOK_ENTRY)

    async with expect_raises_async(vol.Invalid):
        await hass_.services.async_call(logbook.DOMAIN, "log", {}, True)

    await hass_.async_block_till_done()

    expect(len(calls)) == 0


@test
async def filter_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass_: HomeAssistant = Depends(hass_logbook),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test numeric sensors are filtered."""
    registry = er.async_get(hass_)

    entity_id1 = "sensor.bla"
    attributes_1 = None
    entity_id2 = "sensor.blu"
    attributes_2 = {ATTR_UNIT_OF_MEASUREMENT: "cats"}
    entity_id3 = registry.async_get_or_create(
        "sensor",
        "test",
        "unique_3",
        suggested_object_id="bli",
        capabilities={"state_class": SensorStateClass.MEASUREMENT},
    ).entity_id
    attributes_3 = None
    entity_id4 = registry.async_get_or_create(
        "sensor", "test", "unique_4", suggested_object_id="ble"
    ).entity_id
    attributes_4 = None

    hass_.states.async_set(entity_id1, None, attributes_1)
    hass_.states.async_set(entity_id1, 10, attributes_1)
    hass_.states.async_set(entity_id2, None, attributes_2)
    hass_.states.async_set(entity_id2, 10, attributes_2)
    hass_.states.async_set(entity_id3, None, attributes_3)
    hass_.states.async_set(entity_id3, 10, attributes_3)
    hass_.states.async_set(entity_id1, 20, attributes_1)
    hass_.states.async_set(entity_id2, 20, attributes_2)
    hass_.states.async_set(entity_id4, None, attributes_4)
    hass_.states.async_set(entity_id4, 10, attributes_4)

    await async_wait_recording_done(hass_)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 3
    _assert_entry(entries[0], name="bla", entity_id=entity_id1, state="10")
    _assert_entry(entries[1], name="bla", entity_id=entity_id1, state="20")
    _assert_entry(entries[2], name="ble", entity_id=entity_id4, state="10")


@test
async def home_assistant_start_stop_not_grouped(
    _trigger: int = Depends(_trigger_executor),
    hass_: HomeAssistant = Depends(hass_logbook),
) -> None:
    """Test if HA start and stop events are no longer grouped."""
    await async_setup_component(hass_, "homeassistant", {})
    await hass_.async_block_till_done()
    entries = mock_humanify(
        hass_,
        (
            MockRow(EVENT_HOMEASSISTANT_STOP),
            MockRow(EVENT_HOMEASSISTANT_START),
        ),
    )

    expect(len(entries)) == 2
    assert_entry(entries[0], name="Home Assistant", message="stopped", domain=ha.DOMAIN)
    assert_entry(entries[1], name="Home Assistant", message="started", domain=ha.DOMAIN)


@test
async def home_assistant_start(
    _trigger: int = Depends(_trigger_executor),
    hass_: HomeAssistant = Depends(hass_logbook),
) -> None:
    """Test if HA start is not filtered or converted into a restart."""
    await async_setup_component(hass_, "homeassistant", {})
    await hass_.async_block_till_done()
    entity_id = "switch.bla"
    pointA = dt_util.utcnow()

    entries = mock_humanify(
        hass_,
        (
            MockRow(EVENT_HOMEASSISTANT_START),
            create_state_changed_event(pointA, entity_id, 10).row,
        ),
    )

    expect(len(entries)) == 2
    assert_entry(entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN)
    assert_entry(entries[1], pointA, "bla", entity_id=entity_id)


@test
async def process_custom_logbook_entries(
    _trigger: int = Depends(_trigger_executor),
    hass_: HomeAssistant = Depends(hass_logbook),
) -> None:
    """Test if custom log book entries get added as an entry."""
    name = "Nice name"
    message = "has a custom entry"
    entity_id = "sun.sun"

    entries = mock_humanify(
        hass_,
        (
            MockRow(
                logbook.EVENT_LOGBOOK_ENTRY,
                {
                    logbook.ATTR_NAME: name,
                    logbook.ATTR_MESSAGE: message,
                    logbook.ATTR_ENTITY_ID: entity_id,
                },
            ),
        ),
    )

    expect(len(entries)) == 1
    assert_entry(entries[0], name=name, message=message, entity_id=entity_id)


def assert_entry(
    entry, when=None, name=None, message=None, domain=None, entity_id=None
):
    """Assert an entry is what is expected."""
    return _assert_entry(entry, when, name, message, domain, entity_id)


def create_state_changed_event(
    event_time_fired,
    entity_id,
    state,
    attributes=None,
    last_changed=None,
    last_reported=None,
    last_updated=None,
):
    """Create state changed event."""
    old_state = ha.State(
        entity_id,
        "old",
        attributes,
        last_changed=last_changed,
        last_reported=last_reported,
        last_updated=last_updated,
    ).as_dict()
    new_state = ha.State(
        entity_id,
        state,
        attributes,
        last_changed=last_changed,
        last_reported=last_reported,
        last_updated=last_updated,
    ).as_dict()

    return create_state_changed_event_from_old_new(
        entity_id, event_time_fired, old_state, new_state
    )


def create_state_changed_event_from_old_new(
    entity_id, event_time_fired, old_state, new_state
):
    """Create a state changed event from a old and new state."""
    row = EventAsRow(
        row_id=1,
        event_type=PSEUDO_EVENT_STATE_CHANGED,
        event_data="{}",
        time_fired_ts=event_time_fired.timestamp(),
        context_id_bin=None,
        context_user_id_bin=None,
        context_parent_id_bin=None,
        state=new_state and new_state.get("state"),
        entity_id=entity_id,
        icon=None,
        context_only=False,
        data=None,
        context=None,
    )
    return LazyEventPartialState(row, {})


@test
async def logbook_view(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)
    client = await hass_client()
    response = await client.get(f"/api/logbook/{dt_util.utcnow().isoformat()}")
    expect(response.status) == HTTPStatus.OK


@test
async def logbook_view_invalid_start_date_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with an invalid date time."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)
    client = await hass_client()
    response = await client.get("/api/logbook/INVALID")
    expect(response.status) == HTTPStatus.BAD_REQUEST


@test
async def logbook_view_invalid_end_date_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)
    client = await hass_client()
    response = await client.get(
        f"/api/logbook/{dt_util.utcnow().isoformat()}?end_time=INVALID"
    )
    expect(response.status) == HTTPStatus.BAD_REQUEST


@test
async def logbook_view_period_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    _set_utc: None = Depends(set_utc),
) -> None:
    """Test the logbook view with period and entity."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    entity_id_test = "switch.test"
    hass.states.async_set(entity_id_test, STATE_OFF)
    hass.states.async_set(entity_id_test, STATE_ON)
    entity_id_second = "switch.second"
    hass.states.async_set(entity_id_second, STATE_OFF)
    hass.states.async_set(entity_id_second, STATE_ON)
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 2
    expect(response_json[0]["entity_id"]) == entity_id_test
    expect(response_json[1]["entity_id"]) == entity_id_second

    response = await client.get(f"/api/logbook/{start_date.isoformat()}?period=1")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 2
    expect(response_json[0]["entity_id"]) == entity_id_test
    expect(response_json[1]["entity_id"]) == entity_id_second

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?entity=switch.test"
    )
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 1
    expect(response_json[0]["entity_id"]) == entity_id_test

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?period=3&entity=switch.test"
    )
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 1
    expect(response_json[0]["entity_id"]) == entity_id_test

    start = (dt_util.utcnow() + timedelta(days=1)).date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 0

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?entity=switch.test"
    )
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 0

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?period=3&entity=switch.test"
    )
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 1
    expect(response_json[0]["entity_id"]) == entity_id_test


@test
async def logbook_describe_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test teaching logbook about a new event."""

    def _describe(event):
        """Describe an event."""
        return {"name": "Test Name", "message": "tested a message"}

    hass.config.components.add("fake_integration")
    mock_platform(
        hass,
        "fake_integration.logbook",
        Mock(
            async_describe_events=(
                lambda hass, async_describe_event: async_describe_event(
                    "test_domain",
                    "some_event",
                    _describe,
                )
            ),
        ),
    )

    assert await async_setup_component(hass, "logbook", {})
    with freeze_time(dt_util.utcnow() - timedelta(seconds=5)):
        hass.bus.async_fire("some_event")
        await async_wait_recording_done(hass)

    client = await hass_client()
    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    results = await response.json()
    expect(len(results)) == 1
    event = results[0]
    expect(event["name"]) == "Test Name"
    expect(event["message"]) == "tested a message"
    expect(event["domain"]) == "test_domain"


@test
async def exclude_described_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test exclusions of events that are described by another integration."""
    name = "My Automation Rule"
    entity_id = "automation.excluded_rule"
    entity_id2 = "automation.included_rule"
    entity_id3 = "sensor.excluded_domain"

    def _describe(event: Event) -> dict[str, str]:
        """Describe an event."""
        return {
            "name": "Test Name",
            "message": "tested a message",
            "entity_id": event.data[ATTR_ENTITY_ID],
        }

    def async_describe_events(
        hass: HomeAssistant,
        async_describe_event: Callable[
            [str, str, Callable[[Event], dict[str, str]]], None
        ],
    ) -> None:
        """Mock to describe events."""
        async_describe_event("automation", "some_automation_event", _describe)
        async_describe_event("sensor", "some_event", _describe)

    hass.config.components.add("fake_integration")
    mock_platform(
        hass,
        "fake_integration.logbook",
        Mock(async_describe_events=async_describe_events),
    )

    assert await async_setup_component(
        hass,
        logbook.DOMAIN,
        {
            logbook.DOMAIN: {
                CONF_EXCLUDE: {CONF_DOMAINS: ["sensor"], CONF_ENTITIES: [entity_id]}
            }
        },
    )

    with freeze_time(dt_util.utcnow() - timedelta(seconds=5)):
        hass.bus.async_fire(
            "some_automation_event",
            {logbook.ATTR_NAME: name, logbook.ATTR_ENTITY_ID: entity_id},
        )
        hass.bus.async_fire(
            "some_automation_event",
            {logbook.ATTR_NAME: name, logbook.ATTR_ENTITY_ID: entity_id2},
        )
        hass.bus.async_fire(
            "some_event", {logbook.ATTR_NAME: name, logbook.ATTR_ENTITY_ID: entity_id3}
        )
        await async_wait_recording_done(hass)

    client = await hass_client()
    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    results = await response.json()
    expect(len(results)) == 1
    event = results[0]
    expect(event["name"]) == "Test Name"
    expect(event["entity_id"]) == "automation.included_rule"


@test
async def logbook_view_end_time_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with end_time and entity."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    entity_id_test = "switch.test"
    hass.states.async_set(entity_id_test, STATE_OFF)
    hass.states.async_set(entity_id_test, STATE_ON)
    entity_id_second = "switch.second"
    hass.states.async_set(entity_id_second, STATE_OFF)
    hass.states.async_set(entity_id_second, STATE_ON)
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 2
    expect(response_json[0]["entity_id"]) == entity_id_test
    expect(response_json[1]["entity_id"]) == entity_id_second

    end_time = start + timedelta(hours=72)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat(), "entity": "switch.test"},
    )
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()
    expect(len(response_json)) == 1
    expect(response_json[0]["entity_id"]) == entity_id_test

    start = dt_util.utcnow()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=72)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat(), "entity": "switch.test"},
    )
    response_json = await response.json()
    expect(response.status) == HTTPStatus.OK
    expect(len(response_json)) == 1
    expect(response_json[0]["entity_id"]) == entity_id_test


@test
async def logbook_entity_filter_with_automations(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with end_time and entity with automations and scripts."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(entity_id_test, STATE_OFF)
    hass.states.async_set(entity_id_test, STATE_ON)
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF)
    hass.states.async_set(entity_id_second, STATE_ON)

    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: "automation.mock_automation"},
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
    )
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(json_dict[0]["entity_id"]) == entity_id_test
    expect(json_dict[1]["entity_id"]) == entity_id_second
    expect(json_dict[2]["entity_id"]) == "automation.mock_automation"
    expect(json_dict[3]["entity_id"]) == "script.mock_script"
    expect(json_dict[4]["domain"]) == "homeassistant"

    end_time = start + timedelta(hours=72)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={
            "end_time": end_time.isoformat(),
            "entity": "alarm_control_panel.area_001",
        },
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()
    expect(len(json_dict)) == 1
    expect(json_dict[0]["entity_id"]) == entity_id_test

    start = dt_util.utcnow()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=72)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={
            "end_time": end_time.isoformat(),
            "entity": "alarm_control_panel.area_002",
        },
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()
    expect(len(json_dict)) == 1
    expect(json_dict[0]["entity_id"]) == entity_id_second


@test
async def logbook_entity_no_longer_in_state_machine(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with an entity removed from the state machine."""
    await async_setup_component(hass, "logbook", {})
    await async_setup_component(hass, "automation", {})
    await async_setup_component(hass, "script", {})

    await async_wait_recording_done(hass)

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(
        entity_id_test, STATE_OFF, {ATTR_FRIENDLY_NAME: "Alarm Control Panel"}
    )
    hass.states.async_set(
        entity_id_test, STATE_ON, {ATTR_FRIENDLY_NAME: "Alarm Control Panel"}
    )

    await async_wait_recording_done(hass)

    hass.states.async_remove(entity_id_test)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()
    expect(json_dict[0]["name"]) == "area 001"


@test
async def filter_continuous_sensor_values(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    _set_utc: None = Depends(set_utc),
) -> None:
    """Test remove continuous sensor events from logbook."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    entity_id_test = "switch.test"
    hass.states.async_set(entity_id_test, STATE_OFF)
    hass.states.async_set(entity_id_test, STATE_ON)
    entity_id_second = "sensor.bla"
    hass.states.async_set(entity_id_second, STATE_OFF, {"unit_of_measurement": "foo"})
    hass.states.async_set(entity_id_second, STATE_ON, {"unit_of_measurement": "foo"})
    entity_id_third = "light.bla"
    hass.states.async_set(entity_id_third, STATE_OFF, {"unit_of_measurement": "foo"})
    hass.states.async_set(entity_id_third, STATE_ON, {"unit_of_measurement": "foo"})
    entity_id_proximity = "proximity.bla"
    hass.states.async_set(entity_id_proximity, STATE_OFF)
    hass.states.async_set(entity_id_proximity, STATE_ON)
    entity_id_counter = "counter.bla"
    hass.states.async_set(entity_id_counter, STATE_OFF)
    hass.states.async_set(entity_id_counter, STATE_ON)

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()

    expect(len(response_json)) == 2
    expect(response_json[0]["entity_id"]) == entity_id_test
    expect(response_json[1]["entity_id"]) == entity_id_third


@test
async def exclude_new_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    _set_utc: None = Depends(set_utc),
) -> None:
    """Test if events are excluded on first update."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    entity_id = "climate.bla"
    entity_id2 = "climate.blu"

    hass.states.async_set(entity_id, STATE_OFF)
    hass.states.async_set(entity_id2, STATE_ON)
    hass.states.async_set(entity_id2, STATE_OFF)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()

    expect(len(response_json)) == 2
    expect(response_json[0]["entity_id"]) == entity_id2
    expect(response_json[1]["domain"]) == "homeassistant"
    expect(response_json[1]["message"]) == "started"


@test
async def exclude_removed_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    _set_utc: None = Depends(set_utc),
) -> None:
    """Test if events are excluded on last update."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    entity_id = "climate.bla"
    entity_id2 = "climate.blu"

    hass.states.async_set(entity_id, STATE_ON)
    hass.states.async_set(entity_id, STATE_OFF)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set(entity_id2, STATE_ON)
    hass.states.async_set(entity_id2, STATE_OFF)

    hass.states.async_remove(entity_id)
    hass.states.async_remove(entity_id2)

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()

    expect(len(response_json)) == 3
    expect(response_json[0]["entity_id"]) == entity_id
    expect(response_json[1]["domain"]) == "homeassistant"
    expect(response_json[1]["message"]) == "started"
    expect(response_json[2]["entity_id"]) == entity_id2


@test
async def exclude_attribute_changes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
    _set_utc: None = Depends(set_utc),
) -> None:
    """Test if events of attribute changes are filtered."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set("light.kitchen", STATE_OFF)
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 100})
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 200})
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 300})
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 400})
    hass.states.async_set("light.kitchen", STATE_OFF)

    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    response = await client.get(f"/api/logbook/{start_date.isoformat()}")
    expect(response.status) == HTTPStatus.OK
    response_json = await response.json()

    expect(len(response_json)) == 3
    expect(response_json[0]["domain"]) == "homeassistant"
    expect(response_json[1]["entity_id"]) == "light.kitchen"
    expect(response_json[2]["entity_id"]) == "light.kitchen"


@test
async def logbook_entity_context_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with end_time and entity with automations and scripts."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    automation_entity_id_test = "automation.alarm"
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=context,
    )
    hass.states.async_set(
        automation_entity_id_test,
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Alarm Automation"},
        context=context,
    )

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(entity_id_test, STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_test, STATE_ON, context=context)
    await hass.async_block_till_done()
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_second, STATE_ON, context=context)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    await hass.async_add_executor_job(
        logbook.log_entry,
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        "alarm_control_panel.area_003",
        context,
    )
    await hass.async_block_till_done()

    await hass.async_add_executor_job(
        logbook.log_entry,
        hass,
        "mock_name",
        "mock_message",
        "homeassistant",
        None,
        context,
    )
    await hass.async_block_till_done()

    light_turn_off_service_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set("light.switch", STATE_ON)
    await hass.async_block_till_done()

    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "light",
            ATTR_SERVICE: "turn_off",
            ATTR_ENTITY_ID: "light.switch",
        },
        context=light_turn_off_service_context,
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "light.switch", STATE_OFF, context=light_turn_off_service_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(json_dict[0]["entity_id"]) == "automation.alarm"
    assert "context_entity_id" not in json_dict[0]
    expect(json_dict[0]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[1]["entity_id"]) == "script.mock_script"
    expect(json_dict[1]["context_event_type"]) == "automation_triggered"
    expect(json_dict[1]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[1]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[1]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[2]["entity_id"]) == entity_id_test
    expect(json_dict[2]["context_event_type"]) == "automation_triggered"
    expect(json_dict[2]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[2]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[2]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[3]["entity_id"]) == entity_id_second
    expect(json_dict[3]["context_event_type"]) == "automation_triggered"
    expect(json_dict[3]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[3]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[3]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[4]["domain"]) == "homeassistant"

    expect(json_dict[5]["entity_id"]) == "alarm_control_panel.area_003"
    expect(json_dict[5]["context_event_type"]) == "automation_triggered"
    expect(json_dict[5]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[5]["domain"]) == "alarm_control_panel"
    expect(json_dict[5]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[5]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[6]["domain"]) == "homeassistant"
    expect(json_dict[6]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[7]["entity_id"]) == "light.switch"
    expect(json_dict[7]["context_event_type"]) == "call_service"
    expect(json_dict[7]["context_domain"]) == "light"
    expect(json_dict[7]["context_service"]) == "turn_off"
    expect(json_dict[7]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"


@test
async def logbook_context_id_automation_script_started_manually(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook populates context_ids for manually-started scripts."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    automation_entity_id_test = "automation.alarm"
    automation_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVCCC",
        user_id="f400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=automation_context,
    )
    script_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=script_context,
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    script_2_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVEEE",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script"},
        context=script_2_context,
    )
    hass.states.async_set("switch.new", STATE_ON, context=script_2_context)
    hass.states.async_set("switch.new", STATE_OFF, context=script_2_context)

    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(json_dict[0]["entity_id"]) == "automation.alarm"
    assert "context_entity_id" not in json_dict[0]
    expect(json_dict[0]["context_user_id"]) == "f400facee45711eaa9308bfd3d19e474"
    expect(json_dict[0]["context_id"]) == "01GTDGKBCH00GW0X476W5TVCCC"

    expect(json_dict[1]["entity_id"]) == "script.mock_script"
    assert "context_entity_id" not in json_dict[1]
    expect(json_dict[1]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"
    expect(json_dict[1]["context_id"]) == "01GTDGKBCH00GW0X476W5TVAAA"

    expect(json_dict[2]["domain"]) == "homeassistant"

    assert json_dict[3]["entity_id"] is None
    expect(json_dict[3]["name"]) == "Mock script"
    expect(json_dict[3]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"
    expect(json_dict[3]["context_id"]) == "01GTDGKBCH00GW0X476W5TVEEE"

    expect(json_dict[4]["entity_id"]) == "switch.new"
    expect(json_dict[4]["state"]) == "off"
    expect(json_dict[4]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"
    expect(json_dict[4]["context_event_type"]) == "script_started"
    expect(json_dict[4]["context_domain"]) == "script"


@test
async def logbook_entity_context_parent_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view links events via context parent_id."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    automation_entity_id_test = "automation.alarm"
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )

    child_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=child_context,
    )
    hass.states.async_set(
        automation_entity_id_test,
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Alarm Automation"},
        context=child_context,
    )

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(entity_id_test, STATE_OFF, context=child_context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_test, STATE_ON, context=child_context)
    await hass.async_block_till_done()
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF, context=child_context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_second, STATE_ON, context=child_context)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        "alarm_control_panel.area_003",
        child_context,
    )
    await hass.async_block_till_done()

    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "homeassistant",
        None,
        child_context,
    )
    await hass.async_block_till_done()

    light_turn_off_service_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        parent_id="01GTDGKBCH00GW0X476W5TVDDD",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set("light.switch", STATE_ON)
    await hass.async_block_till_done()

    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "light",
            ATTR_SERVICE: "turn_off",
            ATTR_ENTITY_ID: "light.switch",
        },
        context=light_turn_off_service_context,
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "light.switch", STATE_OFF, context=light_turn_off_service_context
    )
    await hass.async_block_till_done()

    missing_parent_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TEDDD",
        parent_id="01GTDGKBCH00GW0X276W5TEDDD",
        user_id="485cacf93ef84d25a99ced3126b921d2",
    )
    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        "alarm_control_panel.area_009",
        missing_parent_context,
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(json_dict[0]["entity_id"]) == "automation.alarm"
    assert "context_entity_id" not in json_dict[0]
    expect(json_dict[0]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[1]["entity_id"]) == "script.mock_script"
    expect(json_dict[1]["context_event_type"]) == "automation_triggered"
    expect(json_dict[1]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[1]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[1]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[2]["entity_id"]) == entity_id_test
    expect(json_dict[2]["context_event_type"]) == "script_started"
    expect(json_dict[2]["context_entity_id"]) == "script.mock_script"
    expect(json_dict[2]["context_entity_id_name"]) == "mock script"
    expect(json_dict[2]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[3]["entity_id"]) == entity_id_second
    expect(json_dict[3]["context_event_type"]) == "script_started"
    expect(json_dict[3]["context_entity_id"]) == "script.mock_script"
    expect(json_dict[3]["context_entity_id_name"]) == "mock script"
    expect(json_dict[3]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[4]["domain"]) == "homeassistant"

    expect(json_dict[5]["entity_id"]) == "alarm_control_panel.area_003"
    expect(json_dict[5]["context_event_type"]) == "script_started"
    expect(json_dict[5]["context_entity_id"]) == "script.mock_script"
    expect(json_dict[5]["domain"]) == "alarm_control_panel"
    expect(json_dict[5]["context_entity_id_name"]) == "mock script"
    expect(json_dict[5]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[6]["domain"]) == "homeassistant"
    expect(json_dict[6]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[7]["entity_id"]) == "light.switch"
    expect(json_dict[7]["context_event_type"]) == "call_service"
    expect(json_dict[7]["context_domain"]) == "light"
    expect(json_dict[7]["context_service"]) == "turn_off"
    expect(json_dict[7]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    expect(json_dict[8]["entity_id"]) == "alarm_control_panel.area_009"
    expect(json_dict[8]["domain"]) == "alarm_control_panel"
    assert "context_event_type" not in json_dict[8]
    assert "context_entity_id" not in json_dict[8]
    assert "context_entity_id_name" not in json_dict[8]
    expect(json_dict[8]["context_user_id"]) == "485cacf93ef84d25a99ced3126b921d2"


@test
async def logbook_context_from_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with end_time and entity with automations and scripts."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    assert await async_setup_component(
        hass,
        "switch",
        {
            "switch": {
                "platform": "template",
                "switches": {
                    "test_template_switch": {
                        "value_template": "{{ states.switch.test_state.state }}",
                        "turn_on": {
                            "service": "switch.turn_on",
                            "entity_id": "switch.test_state",
                        },
                        "turn_off": {
                            "service": "switch.turn_off",
                            "entity_id": "switch.test_state",
                        },
                    }
                },
            }
        },
    )
    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("switch.test_state", STATE_ON)
    await hass.async_block_till_done()

    hass.states.async_set("switch.test_state", STATE_OFF)
    await hass.async_block_till_done()

    switch_turn_off_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set(
        "switch.test_state", STATE_ON, context=switch_turn_off_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start_date + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(json_dict[0]["domain"]) == "homeassistant"
    assert "context_entity_id" not in json_dict[0]

    expect(json_dict[1]["entity_id"]) == "switch.test_template_switch"

    expect(json_dict[2]["entity_id"]) == "switch.test_state"

    expect(json_dict[3]["entity_id"]) == "switch.test_template_switch"
    expect(json_dict[3]["context_entity_id"]) == "switch.test_state"
    expect(json_dict[3]["context_entity_id_name"]) == "test state"

    expect(json_dict[4]["entity_id"]) == "switch.test_state"
    expect(json_dict[4]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    expect(json_dict[5]["entity_id"]) == "switch.test_template_switch"
    expect(json_dict[5]["context_entity_id"]) == "switch.test_state"
    expect(json_dict[5]["context_entity_id_name"]) == "test state"
    expect(json_dict[5]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"


@test
async def logbook_single_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with a single entity."""
    await async_setup_component(hass, "logbook", {})
    assert await async_setup_component(
        hass,
        "switch",
        {
            "switch": {
                "platform": "template",
                "switches": {
                    "test_template_switch": {
                        "value_template": "{{ states.switch.test_state.state }}",
                        "turn_on": {
                            "service": "switch.turn_on",
                            "entity_id": "switch.test_state",
                        },
                        "turn_off": {
                            "service": "switch.turn_off",
                            "entity_id": "switch.test_state",
                        },
                    }
                },
            }
        },
    )
    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("switch.test_state", STATE_ON)
    await hass.async_block_till_done()

    hass.states.async_set("switch.test_state", STATE_OFF)
    await hass.async_block_till_done()

    switch_turn_off_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set(
        "switch.test_state", STATE_ON, context=switch_turn_off_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=switch.test_state"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 2

    expect(json_dict[0]["entity_id"]) == "switch.test_state"

    expect(json_dict[1]["entity_id"]) == "switch.test_state"
    expect(json_dict[1]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"


@test
async def logbook_many_entities_multiple_calls(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with many entities called multiple times."""
    await async_setup_component(hass, "logbook", {})
    await async_setup_component(hass, "automation", {})

    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    for automation_id in range(5):
        hass.bus.async_fire(
            EVENT_AUTOMATION_TRIGGERED,
            {
                ATTR_NAME: f"Mock automation {automation_id}",
                ATTR_ENTITY_ID: f"automation.mock_{automation_id}_automation",
            },
        )
    await async_wait_recording_done(hass)
    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)
    end_time = start + timedelta(hours=24)

    for automation_id in range(5):
        response = await client.get(
            f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=automation.mock_{automation_id}_automation"
        )
        expect(response.status) == HTTPStatus.OK
        json_dict = await response.json()

        expect(len(json_dict)) == 1
        expect(json_dict[0]["entity_id"]) == (
            f"automation.mock_{automation_id}_automation"
        )

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=automation.mock_0_automation,automation.mock_1_automation,automation.mock_2_automation"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 3
    expect(json_dict[0]["entity_id"]) == "automation.mock_0_automation"
    expect(json_dict[1]["entity_id"]) == "automation.mock_1_automation"
    expect(json_dict[2]["entity_id"]) == "automation.mock_2_automation"

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=automation.mock_4_automation,automation.mock_2_automation,automation.mock_0_automation,automation.mock_1_automation"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 4
    expect(json_dict[0]["entity_id"]) == "automation.mock_0_automation"
    expect(json_dict[1]["entity_id"]) == "automation.mock_1_automation"
    expect(json_dict[2]["entity_id"]) == "automation.mock_2_automation"
    expect(json_dict[3]["entity_id"]) == "automation.mock_4_automation"

    response = await client.get(
        f"/api/logbook/{end_time.isoformat()}?end_time={end_time}&entity=automation.mock_4_automation,automation.mock_2_automation,automation.mock_0_automation,automation.mock_1_automation"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()
    expect(len(json_dict)) == 0


@test
async def custom_log_entry_discoverable_via_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if a custom log entry is later discoverable via event."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    logbook.async_log_entry(
        hass,
        "Alarm",
        "is triggered",
        "switch",
        "switch.test_switch",
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time.isoformat()}&entity=switch.test_switch"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 1

    expect(json_dict[0]["name"]) == "Alarm"
    expect(json_dict[0]["message"]) == "is triggered"
    expect(json_dict[0]["entity_id"]) == "switch.test_switch"


@test
async def logbook_multiple_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with multiple entities."""
    await async_setup_component(hass, "logbook", {})
    assert await async_setup_component(
        hass,
        "switch",
        {
            "switch": {
                "platform": "template",
                "switches": {
                    "test_template_switch": {
                        "value_template": "{{ states.switch.test_state.state }}",
                        "turn_on": {
                            "service": "switch.turn_on",
                            "entity_id": "switch.test_state",
                        },
                        "turn_off": {
                            "service": "switch.turn_off",
                            "entity_id": "switch.test_state",
                        },
                    }
                },
            }
        },
    )
    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    hass.states.async_set("switch.test_state", STATE_ON)
    hass.states.async_set("light.test_state", STATE_ON)
    hass.states.async_set("binary_sensor.test_state", STATE_ON)

    await hass.async_block_till_done()

    hass.states.async_set("switch.test_state", STATE_OFF)
    hass.states.async_set("light.test_state", STATE_OFF)
    hass.states.async_set("binary_sensor.test_state", STATE_OFF)

    await hass.async_block_till_done()

    switch_turn_off_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set(
        "switch.test_state", STATE_ON, context=switch_turn_off_context
    )
    hass.states.async_set("light.test_state", STATE_ON, context=switch_turn_off_context)
    hass.states.async_set(
        "binary_sensor.test_state", STATE_ON, context=switch_turn_off_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=switch.test_state,light.test_state"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 4

    expect(json_dict[0]["entity_id"]) == "switch.test_state"

    expect(json_dict[1]["entity_id"]) == "light.test_state"

    expect(json_dict[2]["entity_id"]) == "switch.test_state"
    expect(json_dict[2]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    expect(json_dict[3]["entity_id"]) == "light.test_state"
    expect(json_dict[3]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=binary_sensor.test_state,light.test_state"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 4

    expect(json_dict[0]["entity_id"]) == "light.test_state"

    expect(json_dict[1]["entity_id"]) == "binary_sensor.test_state"

    expect(json_dict[2]["entity_id"]) == "light.test_state"
    expect(json_dict[2]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    expect(json_dict[3]["entity_id"]) == "binary_sensor.test_state"
    expect(json_dict[3]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=light.test_state,binary_sensor.test_state"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(len(json_dict)) == 4

    expect(json_dict[0]["entity_id"]) == "light.test_state"

    expect(json_dict[1]["entity_id"]) == "binary_sensor.test_state"

    expect(json_dict[2]["entity_id"]) == "light.test_state"
    expect(json_dict[2]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"

    expect(json_dict[3]["entity_id"]) == "binary_sensor.test_state"
    expect(json_dict[3]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"


@test
async def logbook_invalid_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with requesting an invalid entity."""
    await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()
    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=invalid"
    )
    expect(response.status) == HTTPStatus.INTERNAL_SERVER_ERROR


@test
async def icon_and_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test to ensure state and custom icons are returned."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set("light.kitchen", STATE_OFF, {"icon": "mdi:chemical-weapon"})
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 100, "icon": "mdi:security"}
    )
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 200, "icon": "mdi:security"}
    )
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 300, "icon": "mdi:security"}
    )
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 400, "icon": "mdi:security"}
    )
    hass.states.async_set("light.kitchen", STATE_OFF, {"icon": "mdi:chemical-weapon"})

    await async_wait_recording_done(hass)

    client = await hass_client()
    response_json = await _async_fetch_logbook(client)

    expect(len(response_json)) == 3
    expect(response_json[0]["domain"]) == "homeassistant"
    expect(response_json[1]["entity_id"]) == "light.kitchen"
    expect(response_json[1]["icon"]) == "mdi:security"
    expect(response_json[1]["state"]) == STATE_ON
    expect(response_json[2]["entity_id"]) == "light.kitchen"
    expect(response_json[2]["icon"]) == "mdi:chemical-weapon"
    expect(response_json[2]["state"]) == STATE_OFF


@test
async def fire_logbook_entries(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test many logbook entry calls."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    for _ in range(10):
        hass.bus.async_fire(
            logbook.EVENT_LOGBOOK_ENTRY,
            {
                logbook.ATTR_NAME: "Alarm",
                logbook.ATTR_MESSAGE: "is triggered",
                logbook.ATTR_DOMAIN: "switch",
                logbook.ATTR_ENTITY_ID: "sensor.xyz",
            },
        )
        hass.bus.async_fire(
            logbook.EVENT_LOGBOOK_ENTRY,
            {},
        )
    hass.bus.async_fire(
        logbook.EVENT_LOGBOOK_ENTRY,
        {
            logbook.ATTR_NAME: "Alarm",
            logbook.ATTR_MESSAGE: "is triggered",
            logbook.ATTR_DOMAIN: "switch",
        },
    )
    await async_wait_recording_done(hass)

    client = await hass_client()
    response_json = await _async_fetch_logbook(client)

    expect(len(response_json)) == 11


@test
async def exclude_events_domain(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if domain is excluded in config."""
    entity_id = "switch.bla"
    entity_id2 = "sensor.blu"

    await async_setup_component(hass, "homeassistant", {})
    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {CONF_EXCLUDE: {CONF_DOMAINS: ["switch", "alexa"]}},
        }
    )
    await async_setup_component(hass, "logbook", config)
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 20)

    await async_wait_recording_done(hass)

    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 2
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="blu", entity_id=entity_id2)


@test
async def exclude_events_domain_glob(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if domain or glob is excluded in config."""
    entity_id = "switch.bla"
    entity_id2 = "sensor.blu"
    entity_id3 = "sensor.excluded"

    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {
                CONF_EXCLUDE: {
                    CONF_DOMAINS: ["switch", "alexa"],
                    CONF_ENTITY_GLOBS: "*.excluded",
                }
            },
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 20)
    hass.states.async_set(entity_id3, None)
    hass.states.async_set(entity_id3, 30)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 2
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="blu", entity_id=entity_id2)


@test
async def include_events_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if entity is included in config."""
    entity_id = "sensor.bla"
    entity_id2 = "sensor.blu"

    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {
                CONF_INCLUDE: {
                    CONF_DOMAINS: ["homeassistant"],
                    CONF_ENTITIES: [entity_id2],
                }
            },
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 20)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 2
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="blu", entity_id=entity_id2)


@test
async def exclude_events_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if entity is excluded in config."""
    entity_id = "sensor.bla"
    entity_id2 = "sensor.blu"

    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {CONF_EXCLUDE: {CONF_ENTITIES: [entity_id]}},
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 20)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)
    expect(len(entries)) == 2
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="blu", entity_id=entity_id2)


@test
async def include_events_domain(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if domain is included in config."""
    assert await async_setup_component(hass, "alexa", {})
    entity_id = "switch.bla"
    entity_id2 = "sensor.blu"
    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {
                CONF_INCLUDE: {CONF_DOMAINS: ["homeassistant", "sensor", "alexa"]}
            },
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.bus.async_fire(
        EVENT_ALEXA_SMART_HOME,
        {"request": {"namespace": "Alexa.Discovery", "name": "Discover"}},
    )
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 20)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 3
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="Amazon Alexa", domain="alexa")
    _assert_entry(entries[2], name="blu", entity_id=entity_id2)


@test
async def include_events_domain_glob(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if domain or glob is included in config."""
    assert await async_setup_component(hass, "alexa", {})
    entity_id = "switch.bla"
    entity_id2 = "sensor.blu"
    entity_id3 = "switch.included"
    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {
                CONF_INCLUDE: {
                    CONF_DOMAINS: ["homeassistant", "sensor", "alexa"],
                    CONF_ENTITY_GLOBS: ["*.included"],
                }
            },
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(
        logbook.EVENT_LOGBOOK_ENTRY,
        {
            logbook.ATTR_NAME: "Alarm",
            logbook.ATTR_MESSAGE: "is triggered",
            logbook.ATTR_ENTITY_ID: "switch.any",
        },
    )
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.bus.async_fire(
        EVENT_ALEXA_SMART_HOME,
        {"request": {"namespace": "Alexa.Discovery", "name": "Discover"}},
    )
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 20)
    hass.states.async_set(entity_id3, None)
    hass.states.async_set(entity_id3, 30)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 4
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="Amazon Alexa", domain="alexa")
    _assert_entry(entries[2], name="blu", entity_id=entity_id2)
    _assert_entry(entries[3], name="included", entity_id=entity_id3)


@test
async def include_exclude_events_no_globs(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if include and exclude is configured."""
    entity_id = "switch.bla"
    entity_id2 = "sensor.blu"
    entity_id3 = "sensor.bli"
    entity_id4 = "sensor.keep"

    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {
                CONF_INCLUDE: {
                    CONF_DOMAINS: ["sensor", "homeassistant"],
                    CONF_ENTITIES: ["switch.bla"],
                },
                CONF_EXCLUDE: {
                    CONF_DOMAINS: ["switch"],
                    CONF_ENTITIES: ["sensor.bli"],
                },
            },
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 10)
    hass.states.async_set(entity_id3, None)
    hass.states.async_set(entity_id3, 10)
    hass.states.async_set(entity_id, 20)
    hass.states.async_set(entity_id2, 20)
    hass.states.async_set(entity_id4, None)
    hass.states.async_set(entity_id4, 10)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 6
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="bla", entity_id=entity_id, state="10")
    _assert_entry(entries[2], name="blu", entity_id=entity_id2, state="10")
    _assert_entry(entries[3], name="bla", entity_id=entity_id, state="20")
    _assert_entry(entries[4], name="blu", entity_id=entity_id2, state="20")
    _assert_entry(entries[5], name="keep", entity_id=entity_id4, state="10")


@test
async def include_exclude_events_with_glob_filters(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test if events are filtered if include and exclude is configured."""
    entity_id = "switch.bla"
    entity_id2 = "sensor.blu"
    entity_id3 = "sensor.bli"
    entity_id4 = "light.included"
    entity_id5 = "switch.included"
    entity_id6 = "sensor.excluded"
    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {
                CONF_INCLUDE: {
                    CONF_DOMAINS: ["sensor", "homeassistant"],
                    CONF_ENTITIES: ["switch.bla"],
                    CONF_ENTITY_GLOBS: ["*.included"],
                },
                CONF_EXCLUDE: {
                    CONF_DOMAINS: ["switch"],
                    CONF_ENTITY_GLOBS: ["*.excluded"],
                    CONF_ENTITIES: ["sensor.bli"],
                },
            },
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)
    hass.states.async_set(entity_id2, None)
    hass.states.async_set(entity_id2, 10)
    hass.states.async_set(entity_id3, None)
    hass.states.async_set(entity_id3, 10)
    hass.states.async_set(entity_id, 20)
    hass.states.async_set(entity_id2, 20)
    hass.states.async_set(entity_id4, None)
    hass.states.async_set(entity_id4, 30)
    hass.states.async_set(entity_id5, None)
    hass.states.async_set(entity_id5, 30)
    hass.states.async_set(entity_id6, None)
    hass.states.async_set(entity_id6, 30)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 7
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="bla", entity_id=entity_id, state="10")
    _assert_entry(entries[2], name="blu", entity_id=entity_id2, state="10")
    _assert_entry(entries[3], name="bla", entity_id=entity_id, state="20")
    _assert_entry(entries[4], name="blu", entity_id=entity_id2, state="20")
    _assert_entry(entries[5], name="included", entity_id=entity_id4, state="30")
    _assert_entry(entries[6], name="included", entity_id=entity_id5, state="30")


@test
async def empty_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test we can handle an empty entity filter."""
    entity_id = "sensor.blu"

    config = logbook.CONFIG_SCHEMA(
        {
            ha.DOMAIN: {},
            logbook.DOMAIN: {},
        }
    )
    await asyncio.gather(
        async_setup_component(hass, "homeassistant", {}),
        async_setup_component(hass, "logbook", config),
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, 10)

    await async_wait_recording_done(hass)
    client = await hass_client()
    entries = await _async_fetch_logbook(client)

    expect(len(entries)) == 2
    _assert_entry(
        entries[0], name="Home Assistant", message="started", domain=ha.DOMAIN
    )
    _assert_entry(entries[1], name="blu", entity_id=entity_id)


@test
async def context_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test we can filter by context."""
    assert await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    entity_id = "switch.blu"
    context = ha.Context()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id, "on", context=context)
    hass.states.async_set(entity_id, "off")
    hass.states.async_set(entity_id, "unknown", context=context)

    await async_wait_recording_done(hass)
    client = await hass_client()

    entries = await _async_fetch_logbook(client, {"context_id": context.id})

    expect(len(entries)) == 2
    _assert_entry(entries[0], entity_id=entity_id, state="on")
    _assert_entry(entries[1], entity_id=entity_id, state="unknown")

    response = await client.get(
        "/api/logbook", params={"context_id": context.id, "entity": entity_id}
    )
    expect(response.status) == HTTPStatus.BAD_REQUEST


async def _async_fetch_logbook(client, params=None):
    if params is None:
        params = {}

    now = dt_util.utcnow()
    start = datetime(now.year, now.month, now.day, tzinfo=dt_util.UTC)
    start_date = datetime(
        start.year, start.month, start.day, tzinfo=dt_util.UTC
    ) - timedelta(hours=24)

    if "end_time" not in params:
        params["end_time"] = (start + timedelta(hours=48)).isoformat()

    response = await client.get(f"/api/logbook/{start_date.isoformat()}", params=params)
    assert response.status == HTTPStatus.OK
    return await response.json()


def _assert_entry(
    entry, when=None, name=None, message=None, domain=None, entity_id=None, state=None
):
    """Assert an entry is what is expected."""
    if when is not None:
        assert when.isoformat() == entry["when"]

    if name is not None:
        assert name == entry["name"]

    if message is not None:
        assert message == entry["message"]

    if domain is not None:
        assert domain == entry["domain"]

    if entity_id is not None:
        assert entity_id == entry["entity_id"]

    if state is not None:
        assert state == entry["state"]


@test
async def get_events(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test logbook get_events."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set("light.kitchen", STATE_OFF)
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 100})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 200})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 300})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 400})
    await hass.async_block_till_done()
    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    hass.states.async_set("light.kitchen", STATE_OFF, context=context)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["result"]) == []

    await client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["sensor.test"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 2
    expect(response["result"]) == []

    await client.send_json(
        {
            "id": 3,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 3

    results = response["result"]
    expect(results[0]["entity_id"]) == "light.kitchen"
    expect(results[0]["state"]) == "on"
    expect(results[1]["entity_id"]) == "light.kitchen"
    expect(results[1]["state"]) == "off"

    await client.send_json(
        {
            "id": 4,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 4

    results = response["result"]
    expect(len(results)) == 3
    expect(results[0]["message"]) == "started"
    expect(results[1]["entity_id"]) == "light.kitchen"
    expect(results[1]["state"]) == "on"
    assert isinstance(results[1]["when"], float)
    expect(results[2]["entity_id"]) == "light.kitchen"
    expect(results[2]["state"]) == "off"
    assert isinstance(results[2]["when"], float)

    await client.send_json(
        {
            "id": 5,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "context_id": "01GTDGKBCH00GW0X476W5TVAAA",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 5

    results = response["result"]
    expect(len(results)) == 1
    expect(results[0]["entity_id"]) == "light.kitchen"
    expect(results[0]["state"]) == "off"
    assert isinstance(results[0]["when"], float)


@test
async def get_events_future_start_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test get_events with a future start time."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)
    future = dt_util.utcnow() + timedelta(hours=10)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": future.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 1

    results = response["result"]
    assert isinstance(results, list)
    expect(len(results)) == 0


@test
async def get_events_bad_start_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test get_events bad start time."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": "cats",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    expect(response["error"]["code"]) == "invalid_start_time"


@test
async def get_events_bad_end_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test get_events bad end time."""
    now = dt_util.utcnow()
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "end_time": "dogs",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    expect(response["error"]["code"]) == "invalid_end_time"


@test
async def get_events_invalid_filters(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test get_events invalid filters."""
    await async_setup_component(hass, "logbook", {})
    await async_recorder_block_till_done(hass)

    client = await hass_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "entity_ids": [],
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    expect(response["error"]["code"]) == "invalid_format"
    await client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "device_ids": [],
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    expect(response["error"]["code"]) == "invalid_format"


@test
async def get_events_with_device_ids(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test logbook get_events for device ids."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    entry = MockConfigEntry(domain="test", data={"first": True}, options=None)
    entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        sw_version="sw-version",
        name="device name",
        manufacturer="manufacturer",
        model="model",
        suggested_area="Game Room",
    )

    class MockLogbookPlatform:
        """Mock a logbook platform."""

        @ha.callback
        def async_describe_events(
            hass: HomeAssistant,  # noqa: N805
            async_describe_event: Callable[
                [str, str, Callable[[Event], dict[str, str]]], None
            ],
        ) -> None:
            """Describe logbook events."""

            @ha.callback
            def async_describe_test_event(event: Event) -> dict[str, str]:
                """Describe mock logbook event."""
                return {
                    "name": "device name",
                    "message": "is on fire",
                }

            async_describe_event("test", "mock_event", async_describe_test_event)

    logbook._process_logbook_platform(hass, "test", MockLogbookPlatform)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.bus.async_fire("mock_event", {"device_id": device.id})

    hass.states.async_set("light.kitchen", STATE_OFF)
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 100})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 200})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 300})
    await hass.async_block_till_done()
    hass.states.async_set("light.kitchen", STATE_ON, {"brightness": 400})
    await hass.async_block_till_done()
    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    hass.states.async_set("light.kitchen", STATE_OFF, context=context)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)
    client = await hass_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "device_ids": [device.id],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 1

    results = response["result"]
    expect(len(results)) == 1
    expect(results[0]["name"]) == "device name"
    expect(results[0]["message"]) == "is on fire"
    assert isinstance(results[0]["when"], float)

    await client.send_json(
        {
            "id": 2,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
            "entity_ids": ["light.kitchen"],
            "device_ids": [device.id],
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 2

    results = response["result"]
    expect(results[0]["domain"]) == "test"
    expect(results[0]["message"]) == "is on fire"
    expect(results[0]["name"]) == "device name"
    expect(results[1]["entity_id"]) == "light.kitchen"
    expect(results[1]["state"]) == "on"
    expect(results[2]["entity_id"]) == "light.kitchen"
    expect(results[2]["state"]) == "off"

    await client.send_json(
        {
            "id": 3,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 3

    results = response["result"]
    expect(len(results)) == 4
    expect(results[0]["message"]) == "started"
    expect(results[1]["name"]) == "device name"
    expect(results[1]["message"]) == "is on fire"
    assert isinstance(results[1]["when"], float)
    expect(results[2]["entity_id"]) == "light.kitchen"
    expect(results[2]["state"]) == "on"
    assert isinstance(results[2]["when"], float)
    expect(results[3]["entity_id"]) == "light.kitchen"
    expect(results[3]["state"]) == "off"
    assert isinstance(results[3]["when"], float)


@test
async def logbook_select_entities_context_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test the logbook view with end_time and entity with automations and scripts."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook", "automation", "script")
        ]
    )

    await async_recorder_block_till_done(hass)

    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    automation_entity_id_test = "automation.alarm"
    hass.bus.async_fire(
        EVENT_AUTOMATION_TRIGGERED,
        {ATTR_NAME: "Mock automation", ATTR_ENTITY_ID: automation_entity_id_test},
        context=context,
    )
    hass.bus.async_fire(
        EVENT_SCRIPT_STARTED,
        {ATTR_NAME: "Mock script", ATTR_ENTITY_ID: "script.mock_script"},
        context=context,
    )
    hass.states.async_set(
        automation_entity_id_test,
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Alarm Automation"},
        context=context,
    )

    entity_id_test = "alarm_control_panel.area_001"
    hass.states.async_set(entity_id_test, STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_test, STATE_ON, context=context)
    await hass.async_block_till_done()
    entity_id_second = "alarm_control_panel.area_002"
    hass.states.async_set(entity_id_second, STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(entity_id_second, STATE_ON, context=context)
    await hass.async_block_till_done()
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    entity_id_third = "alarm_control_panel.area_003"

    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "alarm_control_panel",
        entity_id_third,
        context,
    )
    await hass.async_block_till_done()

    logbook.async_log_entry(
        hass,
        "mock_name",
        "mock_message",
        "homeassistant",
        None,
        context,
    )
    await hass.async_block_till_done()

    light_turn_off_service_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVBFC",
        user_id="9400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set("light.switch", STATE_ON)
    await hass.async_block_till_done()

    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "light",
            ATTR_SERVICE: "turn_off",
            ATTR_ENTITY_ID: "light.switch",
        },
        context=light_turn_off_service_context,
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "light.switch", STATE_OFF, context=light_turn_off_service_context
    )
    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)

    end_time = start + timedelta(hours=24)
    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity={entity_id_test},{entity_id_second},{entity_id_third},light.switch"
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    expect(json_dict[0]["entity_id"]) == entity_id_test
    expect(json_dict[0]["context_event_type"]) == "automation_triggered"
    expect(json_dict[0]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[0]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[0]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[1]["entity_id"]) == entity_id_second
    expect(json_dict[1]["context_event_type"]) == "automation_triggered"
    expect(json_dict[1]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[1]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[1]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[2]["entity_id"]) == "alarm_control_panel.area_003"
    expect(json_dict[2]["context_event_type"]) == "automation_triggered"
    expect(json_dict[2]["context_entity_id"]) == "automation.alarm"
    expect(json_dict[2]["domain"]) == "alarm_control_panel"
    expect(json_dict[2]["context_entity_id_name"]) == "Alarm Automation"
    expect(json_dict[2]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"

    expect(json_dict[3]["entity_id"]) == "light.switch"
    expect(json_dict[3]["context_event_type"]) == "call_service"
    expect(json_dict[3]["context_domain"]) == "light"
    expect(json_dict[3]["context_service"]) == "turn_off"
    expect(json_dict[3]["context_user_id"]) == "9400facee45711eaa9308bfd3d19e474"


@test
async def get_events_with_context_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test logbook get_events with a context state."""
    now = dt_util.utcnow()
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )
    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.states.async_set("binary_sensor.is_light", STATE_ON)
    hass.states.async_set("light.kitchen1", STATE_OFF)
    hass.states.async_set("light.kitchen2", STATE_OFF)

    context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )
    hass.states.async_set("binary_sensor.is_light", STATE_OFF, context=context)
    await hass.async_block_till_done()
    hass.states.async_set(
        "light.kitchen1", STATE_ON, {"brightness": 100}, context=context
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        "light.kitchen2", STATE_ON, {"brightness": 200}, context=context
    )
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_ws_client()

    await client.send_json(
        {
            "id": 1,
            "type": "logbook/get_events",
            "start_time": now.isoformat(),
        }
    )
    response = await client.receive_json()
    assert response["success"]
    expect(response["id"]) == 1
    results = response["result"]
    expect(results[1]["entity_id"]) == "binary_sensor.is_light"
    expect(results[1]["state"]) == "off"
    assert "context_state" not in results[1]
    expect(results[2]["entity_id"]) == "light.kitchen1"
    expect(results[2]["state"]) == "on"
    expect(results[2]["context_entity_id"]) == "binary_sensor.is_light"
    expect(results[2]["context_state"]) == "off"
    expect(results[2]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"
    assert "context_event_type" not in results[2]
    expect(results[3]["entity_id"]) == "light.kitchen2"
    expect(results[3]["state"]) == "on"
    expect(results[3]["context_entity_id"]) == "binary_sensor.is_light"
    expect(results[3]["context_state"]) == "off"
    expect(results[3]["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"
    assert "context_event_type" not in results[3]


@test
async def logbook_with_empty_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a empty configuration."""
    assert await async_setup_component(
        hass,
        logbook.DOMAIN,
        {
            logbook.DOMAIN: {},
            recorder.DOMAIN: {},
        },
    )
    await hass.async_block_till_done()


@test
async def logbook_with_non_iterable_entity_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle a non-iterable entity filter."""
    assert await async_setup_component(
        hass,
        logbook.DOMAIN,
        {
            logbook.DOMAIN: {
                CONF_EXCLUDE: {
                    CONF_ENTITIES: ["light.additional_excluded"],
                }
            },
            recorder.DOMAIN: {
                CONF_EXCLUDE: {
                    CONF_ENTITIES: None,
                    CONF_DOMAINS: None,
                    CONF_ENTITY_GLOBS: None,
                }
            },
        },
    )
    await hass.async_block_till_done()


@test
async def logbook_user_id_from_parent_context(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test user attribution is inherited through the full context chain."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    await async_recorder_block_till_done(hass)

    setup_thermostat_context_test_entities(hass)
    await hass.async_block_till_done()

    parent_context, _ = simulate_thermostat_context_chain(hass)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)
    end_time = start_date + timedelta(hours=24)

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    assert_thermostat_context_chain_events(json_dict, parent_context)


@test
async def logbook_user_id_from_parent_context_state_changes_only(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> None:
    """Test user attribution is inherited when only state changes are present."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    await async_recorder_block_till_done(hass)

    hass.states.async_set(
        "climate.living_room",
        "off",
        {ATTR_FRIENDLY_NAME: "Living Room Thermostat"},
    )
    hass.states.async_set("switch.heater", STATE_OFF)
    await hass.async_block_till_done()

    parent_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id="b400facee45711eaa9308bfd3d19e474",
    )

    hass.states.async_set(
        "climate.living_room",
        "heat",
        {ATTR_FRIENDLY_NAME: "Living Room Thermostat"},
        context=parent_context,
    )
    await hass.async_block_till_done()

    child_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id="01GTDGKBCH00GW0X476W5TVAAA",
    )

    hass.states.async_set(
        "switch.heater",
        STATE_ON,
        {ATTR_FRIENDLY_NAME: "Heater"},
        context=child_context,
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "climate.living_room",
        "heat",
        {ATTR_FRIENDLY_NAME: "Living Room Thermostat"},
        context=child_context,
    )
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    client = await hass_client()

    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)
    end_time = start_date + timedelta(hours=24)

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}",
        params={"end_time": end_time.isoformat()},
    )
    expect(response.status) == HTTPStatus.OK
    json_dict = await response.json()

    heater_entries = [
        entry for entry in json_dict if entry.get("entity_id") == "switch.heater"
    ]
    expect(len(heater_entries)) == 1

    heater_entry = heater_entries[0]
    expect(heater_entry["context_entity_id"]) == "climate.living_room"
    expect(heater_entry["context_entity_id_name"]) == "Living Room Thermostat"
    expect(heater_entry["context_state"]) == "heat"
    expect(heater_entry["context_user_id"]) == "b400facee45711eaa9308bfd3d19e474"


@test
async def context_user_ids_lru_eviction(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the parent context user-id cache is bounded by LRU eviction."""
    user_id = "b400facee45711eaa9308bfd3d19e474"
    early_parent_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVAAA",
        user_id=user_id,
    )
    child_context = ha.Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id=early_parent_context.id,
    )

    logbook_run = logbook.processor.LogbookRun(
        context_lookup={None: None},
        external_events={},
        event_cache=logbook.processor.EventCache({}),
        entity_name_cache=logbook.processor.EntityNameCache(hass),
        include_entity_name=True,
        timestamp=False,
        memoize_new_contexts=False,
        for_live_stream=True,
    )
    context_augmenter = logbook.processor.ContextAugmenter(logbook_run)
    ent_reg = er.async_get(hass)

    processor = logbook.processor.EventProcessor.__new__(
        logbook.processor.EventProcessor
    )
    processor.hass = hass
    processor.ent_reg = ent_reg
    processor.logbook_run = logbook_run
    processor.context_augmenter = context_augmenter

    hass.states.async_set("switch.heater", STATE_OFF)
    await hass.async_block_till_done()

    parent_row = MockRow(
        EVENT_CALL_SERVICE,
        {
            ATTR_DOMAIN: "climate",
            ATTR_SERVICE: "set_hvac_mode",
            "service_data": {ATTR_ENTITY_ID: "climate.living_room"},
        },
        context=early_parent_context,
    )
    parent_row.context_only = True
    parent_row.icon = None
    processor.humanify([parent_row])
    assert (
        ulid_to_bytes_or_none(early_parent_context.id) in logbook_run.context_user_ids
    )

    filler_rows = []
    for index in range(logbook.processor.MAX_CONTEXT_USER_IDS_CACHE + 1):
        filler_context = ha.Context(
            user_id=f"ffffffff{index:024x}"[:32],
        )
        filler_row = MockRow(
            EVENT_CALL_SERVICE,
            {
                ATTR_DOMAIN: "test",
                ATTR_SERVICE: "noop",
                "service_data": {},
            },
            context=filler_context,
        )
        filler_row.context_only = True
        filler_row.icon = None
        filler_rows.append(filler_row)
    processor.humanify(filler_rows)

    expect(len(logbook_run.context_user_ids)) == (
        logbook.processor.MAX_CONTEXT_USER_IDS_CACHE
    )
    assert (
        ulid_to_bytes_or_none(early_parent_context.id)
        not in logbook_run.context_user_ids
    )

    child_row = MockRow(
        PSEUDO_EVENT_STATE_CHANGED,
        context=child_context,
    )
    child_row.state = STATE_ON
    child_row.entity_id = "switch.heater"
    child_row.icon = None
    results = processor.humanify([child_row])

    heater_entries = [e for e in results if e.get("entity_id") == "switch.heater"]
    expect(len(heater_entries)) == 1
    assert "context_user_id" not in heater_entries[0]


@test
async def parent_user_attribution_does_not_use_origin_event_fallback(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that parent context lookup doesn't fall back to origin_event."""
    wrong_user_id = "aaaaaaaaaaa711eaa9308bfd3d19e474"
    parent_context = Context(id="01GTDGKBCH00GW0X476W5TVAAA")

    child_context = Context(
        id="01GTDGKBCH00GW0X476W5TVDDD",
        parent_id=parent_context.id,
        user_id=wrong_user_id,
    )
    Event(EVENT_CALL_SERVICE, {}, context=child_context)
    assert child_context.origin_event is not None

    hass.states.async_set("switch.heater", STATE_OFF)
    await hass.async_block_till_done()

    logbook_run = logbook.processor.LogbookRun(
        context_lookup={None: None},
        external_events={},
        event_cache=logbook.processor.EventCache({}),
        entity_name_cache=logbook.processor.EntityNameCache(hass),
        include_entity_name=True,
        timestamp=False,
        memoize_new_contexts=False,
    )
    context_augmenter = logbook.processor.ContextAugmenter(logbook_run)
    ent_reg = er.async_get(hass)

    processor = logbook.processor.EventProcessor.__new__(
        logbook.processor.EventProcessor
    )
    processor.hass = hass
    processor.ent_reg = ent_reg
    processor.logbook_run = logbook_run
    processor.context_augmenter = context_augmenter

    child_row = EventAsRow(
        row_id=1,
        event_type=PSEUDO_EVENT_STATE_CHANGED,
        event_data=None,
        time_fired_ts=dt_util.utcnow().timestamp(),
        context_id_bin=ulid_to_bytes_or_none(child_context.id),
        context_user_id_bin=None,
        context_parent_id_bin=ulid_to_bytes_or_none(child_context.parent_id),
        state=STATE_ON,
        entity_id="switch.heater",
        icon=None,
        context_only=False,
        data={},
        context=child_context,
    )

    results = processor.humanify([child_row])

    heater_entries = [e for e in results if e.get("entity_id") == "switch.heater"]
    expect(len(heater_entries)) == 1
    assert "context_user_id" not in heater_entries[0]
