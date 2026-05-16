"""Unit tests for the Todoist calendar platform (tryke port)."""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, patch
import urllib
import zoneinfo

from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.models import Collaborator, Due, Label, Project, Section, Task
from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components.todoist.const import (
    ASSIGNEE,
    CONTENT,
    DOMAIN,
    LABELS,
    PROJECT_NAME,
    SECTION_NAME,
    SERVICE_NEW_TASK,
)
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import (
    PROJECT_ID,
    SECTION_ID,
    SUMMARY,
    TOKEN,
    make_api_due,
    make_api_response,
    make_api_task,
    mock_api,
    setup_yaml_calendar_platform,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async

# Set our timezone to CST/Regina so we can check calculations
# This keeps UTC-6 all year round
TZ_NAME = "America/Regina"
TIMEZONE = zoneinfo.ZoneInfo(TZ_NAME)


def get_events_url(entity: str, start: str, end: str) -> str:
    """Create a url to get events during the specified time range."""
    return f"/api/calendars/{entity}?start={urllib.parse.quote(start)}&end={urllib.parse.quote(end)}"


def get_events_response(start: dict[str, str], end: dict[str, str]) -> dict[str, Any]:
    """Return an event response with a single task."""
    return {
        "start": start,
        "end": end,
        "summary": SUMMARY,
        "description": None,
        "location": None,
        "uid": None,
        "recurrence_id": None,
        "rrule": None,
    }


def _build_api_with_tasks(tasks: list[Task]) -> AsyncMock:
    """Construct a fresh AsyncMock TodoistAPIAsync wired with ``tasks``."""
    api = AsyncMock(spec=TodoistAPIAsync)
    api.get_projects.side_effect = make_api_response(
        [
            Project(
                id=PROJECT_ID,
                color="blue",
                is_favorite=False,
                name="Name",
                is_shared=False,
                is_archived=False,
                is_collapsed=False,
                is_inbox_project=False,
                can_assign_tasks=False,
                order=1,
                parent_id=None,
                view_style="list",
                description="",
                created_at="2021-01-01",
                updated_at="2021-01-01",
            )
        ]
    )
    api.get_sections.side_effect = make_api_response(
        [
            Section(
                id=SECTION_ID,
                project_id=PROJECT_ID,
                name="Section Name",
                order=1,
                is_collapsed=False,
            )
        ]
    )
    api.get_labels.side_effect = make_api_response(
        [Label(id="1", name="Label1", color="1", order=1, is_favorite=False)]
    )
    api.get_collaborators.side_effect = make_api_response(
        [Collaborator(email="user@gmail.com", id="1", name="user")]
    )
    api.get_tasks.side_effect = make_api_response(tasks)
    return api


@fixture
def _trigger_executor() -> int:
    """Force the async/Depends executor for this module."""
    return 0


@fixture
def freeze_calendar_time() -> AsyncGenerator[None]:
    """Freeze time for calendar tests (replaces autouse pytest fixture)."""
    with freeze_time("2024-05-24 12:00:00"):
        yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@test
async def calendar_entity_unique_id(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique id is set to project id."""
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(hass, api, {})
    entity = entity_registry.async_get("calendar.name")
    expect(entity.unique_id).to_equal(PROJECT_ID)


@test
async def update_entity_for_custom_project_with_labels_on(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test that the calendar's state is on for a custom project using labels."""
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(
        hass,
        api,
        {"custom_projects": [{"name": "All projects", "labels": ["Label1"]}]},
    )
    await async_update_entity(hass, "calendar.all_projects")
    state = hass.states.get("calendar.all_projects")
    expect(state.attributes["labels"]).to_equal(["Label1"])
    expect(state.state).to_equal("on")


@test
async def update_entity_for_custom_project_no_due_date_on(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a task without an explicit due date is considered to be in an on state."""
    api = _build_api_with_tasks([make_api_task(due=None)])
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(hass, api, {})
    await async_update_entity(hass, "calendar.name")
    state = hass.states.get("calendar.name")
    expect(state.state).to_equal("on")


# Legacy fixture order had ``due`` evaluated BEFORE ``set_time_zone`` ran;
# we mirror that by constructing the Due at module load.
_FUTURE_DUE = make_api_due(
    date=(
        datetime(day=15, month=10, year=2025, hour=23, minute=45, tzinfo=TIMEZONE)
        + timedelta(days=3)
    ).strftime("%Y-%m-%d"),
    is_recurring=False,
    string="3 days from today",
)


@test
async def update_entity_for_calendar_with_due_date_in_the_future(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that a task with a due date in the future has on state and correct end_time."""
    api = _build_api_with_tasks([make_api_task(due=_FUTURE_DUE)])
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(hass, api, {})
    await async_update_entity(hass, "calendar.name")
    state = hass.states.get("calendar.name")
    expect(state.state).to_equal("on")

    expected_end_time = (
        datetime(day=15, month=10, year=2025, hour=23, minute=45) + timedelta(days=3)
    ).strftime("%Y-%m-%d 00:00:00")
    expect(state.attributes["end_time"]).to_equal(expected_end_time)


@test
async def failed_coordinator_update(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test a failed data coordinator update is handled correctly."""
    await hass.config.async_set_time_zone(TZ_NAME)
    api.get_tasks.side_effect = Exception("API error")

    with patch(
        "homeassistant.components.todoist.calendar.TodoistAPIAsync", return_value=api
    ):
        assert await setup.async_setup_component(
            hass,
            "calendar",
            {
                "calendar": {
                    "platform": DOMAIN,
                    CONF_TOKEN: "token",
                    "custom_projects": [{"name": "All projects", "labels": ["Label1"]}],
                }
            },
        )
        await hass.async_block_till_done()

    await async_update_entity(hass, "calendar.all_projects")
    state = hass.states.get("calendar.all_projects")
    expect(state).to_be(None)


@test
async def calendar_custom_project_unique_id(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique id is None for any custom projects."""
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(
        hass, api, {"custom_projects": [{"name": "All projects"}]}
    )
    entity = entity_registry.async_get("calendar.all_projects")
    expect(entity).to_be(None)


@test.cases(
    test.case(
        "included",
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-28T00:00:00.000Z",
        end="2023-04-01T00:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "exact",
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-30T06:00:00.000Z",
        end="2023-03-31T06:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "overlap_start",
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-29T08:00:00.000Z",
        end="2023-03-30T08:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "overlap_end",
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-30T08:00:00.000Z",
        end="2023-03-31T08:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "after",
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-31T08:00:00.000Z",
        end="2023-04-01T08:00:00.000Z",
        expected_response=[],
    ),
    test.case(
        "before",
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-29T06:00:00.000Z",
        end="2023-03-30T06:00:00.000Z",
        expected_response=[],
    ),
)
async def all_day_event(
    due: Due,
    start: str,
    end: str,
    expected_response: list[dict[str, Any]],
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test for an all day calendar event."""
    await hass.config.async_set_time_zone(TZ_NAME)
    api = _build_api_with_tasks([make_api_task(due=due)])
    await setup_yaml_calendar_platform(hass, api, {})
    client = await hass_client()
    response = await client.get(get_events_url("calendar.name", start, end))
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(expected_response)


@test
async def create_task_service_call(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test api is called correctly after a new task service call."""
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(hass, api, {})
    await hass.services.async_call(
        DOMAIN,
        SERVICE_NEW_TASK,
        {ASSIGNEE: "user", CONTENT: "task", LABELS: ["Label1"], PROJECT_NAME: "Name"},
    )
    await hass.async_block_till_done()

    api.add_task.assert_called_with(
        "task", project_id=PROJECT_ID, labels=["Label1"], assignee_id="1"
    )


@test
async def create_task_service_call_raises(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test adding an item to an invalid project raises an error."""
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(hass, api, {})
    async with expect_raises_async(ServiceValidationError, match="project_invalid"):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_NEW_TASK,
            {
                ASSIGNEE: "user",
                CONTENT: "task",
                LABELS: ["Label1"],
                PROJECT_NAME: "Missing Project",
            },
            blocking=True,
        )


@test
async def create_task_service_call_with_section(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_api),
) -> None:
    """Test api is called correctly when section is included."""
    await hass.config.async_set_time_zone(TZ_NAME)
    await setup_yaml_calendar_platform(hass, api, {})
    await hass.services.async_call(
        DOMAIN,
        SERVICE_NEW_TASK,
        {
            ASSIGNEE: "user",
            CONTENT: "task",
            LABELS: ["Label1"],
            PROJECT_NAME: "Name",
            SECTION_NAME: "Section Name",
        },
    )
    await hass.async_block_till_done()

    api.add_task.assert_called_with(
        "task",
        project_id=PROJECT_ID,
        section_id=SECTION_ID,
        labels=["Label1"],
        assignee_id="1",
    )


@test.cases(
    test.case(
        "in_local_timezone",
        due=make_api_due(
            date="2023-03-31T00:00:00Z",
            is_recurring=False,
            string="Mar 30 6:00 PM",
            timezone="America/Regina",
        ),
    ),
    test.case(
        "in_other_timezone",
        due=make_api_due(
            date="2023-03-31T00:00:00Z",
            is_recurring=False,
            string="Mar 30 7:00 PM",
            timezone="America/Los_Angeles",
        ),
    ),
    test.case(
        "floating",
        due=make_api_due(
            date="2023-03-30T18:00:00",
            is_recurring=False,
            string="Mar 30 6:00 PM",
        ),
    ),
)
async def task_due_datetime(
    due: Due,
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test for task due at a specific time, using different time formats."""
    await hass.config.async_set_time_zone(TZ_NAME)
    api = _build_api_with_tasks([make_api_task(due=due)])
    await setup_yaml_calendar_platform(hass, api, {})
    client = await hass_client()

    has_task_response = [
        get_events_response(
            {"dateTime": "2023-03-30T18:00:00-06:00"},
            {"dateTime": "2023-03-31T18:00:00-06:00"},
        )
    ]

    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-30T08:00:00.000Z", "2023-03-31T08:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(has_task_response)

    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-29T20:00:00.000Z", "2023-03-31T02:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(has_task_response)

    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-31T20:00:00.000Z", "2023-04-01T02:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(has_task_response)

    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-31T10:00:00.000Z", "2023-03-31T11:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(has_task_response)

    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-28T00:00:00.000Z", "2023-03-29T00:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal([])

    response = await client.get(
        get_events_url(
            "calendar.name", "2023-04-01T07:00:00.000Z", "2023-04-02T07:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal([])


# Module-load-time computation matches the legacy pre-tz-set parametrize evaluation.
_NOW_FOR_FILTER = dt_util.now()


@test.cases(
    test.case(
        "in_labels_whitelist",
        todoist_config={"custom_projects": [{"name": "Test", "labels": ["Label1"]}]},
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-28T00:00:00.000Z",
        end="2023-04-01T00:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "not_in_labels_whitelist",
        todoist_config={"custom_projects": [{"name": "Test", "labels": ["custom"]}]},
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-28T00:00:00.000Z",
        end="2023-04-01T00:00:00.000Z",
        expected_response=[],
    ),
    test.case(
        "in_include_projects",
        todoist_config={
            "custom_projects": [{"name": "Test", "include_projects": ["Name"]}]
        },
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-28T00:00:00.000Z",
        end="2023-04-01T00:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "in_due_date_days",
        todoist_config={"custom_projects": [{"name": "Test", "due_date_days": 1}]},
        due=make_api_due(date="2023-03-30", is_recurring=False, string="Mar 30"),
        start="2023-03-28T00:00:00.000Z",
        end="2023-04-01T00:00:00.000Z",
        expected_response=[
            get_events_response({"date": "2023-03-30"}, {"date": "2023-03-31"})
        ],
    ),
    test.case(
        "not_in_due_date_days",
        todoist_config={"custom_projects": [{"name": "Test", "due_date_days": 1}]},
        due=make_api_due(
            date=(_NOW_FOR_FILTER + timedelta(days=2)).strftime("%Y-%m-%d"),
            is_recurring=False,
            string="Mar 30",
        ),
        start=_NOW_FOR_FILTER.isoformat(),
        end=(_NOW_FOR_FILTER + timedelta(days=5)).isoformat(),
        expected_response=[],
    ),
)
async def events_filtered_for_custom_projects(
    todoist_config: dict[str, Any],
    due: Due,
    start: str,
    end: str,
    expected_response: list[dict[str, Any]],
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test we filter out tasks from custom projects based on their config."""
    await hass.config.async_set_time_zone(TZ_NAME)
    api = _build_api_with_tasks([make_api_task(due=due)])
    await setup_yaml_calendar_platform(hass, api, todoist_config)
    client = await hass_client()
    response = await client.get(get_events_url("calendar.test", start, end))
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(expected_response)


# ``test_config_entry`` uses a single parametrize case with a specific due and
# setup_platform=None - inline that case using a config-entry-based integration setup.
_CONFIG_ENTRY_DUE = make_api_due(
    date="2023-03-31T00:00:00Z",
    is_recurring=False,
    string="Mar 30 6:00 PM",
    timezone="America/Regina",
)


@test
async def config_entry(
    _frozen: None = Depends(freeze_calendar_time),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test for a calendar created with a config entry."""
    await hass.config.async_set_time_zone(TZ_NAME)
    api = _build_api_with_tasks([make_api_task(due=_CONFIG_ENTRY_DUE)])
    config_entry_obj = MockConfigEntry(
        domain=DOMAIN, unique_id=TOKEN, data={CONF_TOKEN: TOKEN}
    )
    config_entry_obj.add_to_hass(hass)
    with (
        patch("homeassistant.components.todoist.TodoistAPIAsync", return_value=api),
        patch(
            "homeassistant.components.todoist.PLATFORMS",
            [Platform.CALENDAR],
        ),
    ):
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    await async_update_entity(hass, "calendar.name")
    state = hass.states.get("calendar.name")
    expect(state).not_.to_be(None)

    client = await hass_client()
    response = await client.get(
        get_events_url(
            "calendar.name", "2023-03-30T08:00:00.000Z", "2023-03-31T08:00:00.000Z"
        ),
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.json()).to_equal(
        [
            get_events_response(
                {"dateTime": "2023-03-30T18:00:00-06:00"},
                {"dateTime": "2023-03-31T18:00:00-06:00"},
            )
        ]
    )
