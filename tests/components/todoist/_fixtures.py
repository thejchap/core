"""Tryke fixtures for the todoist tests."""

from collections.abc import AsyncGenerator, Callable, Generator
from http import HTTPStatus
from typing import TypeVar
from unittest.mock import AsyncMock, patch

from requests.exceptions import HTTPError
from requests.models import Response
from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.models import Collaborator, Due, Label, Project, Section, Task
from tryke import Depends, fixture

from homeassistant.components.todoist.const import DOMAIN
from homeassistant.const import CONF_TOKEN

from tests.common import MockConfigEntry

T = TypeVar("T")

PROJECT_ID = "project-id-1"
SECTION_ID = "section-id-1"
SUMMARY = "A task"
TOKEN = "some-token"


async def _async_generator(items: list[T]) -> AsyncGenerator[list[T]]:
    """Yield items as a single page."""
    yield items


def make_api_response(items: list[T]) -> Callable[[], AsyncGenerator[list[T]]]:
    """Create a callable that returns a fresh async generator each time."""

    async def _generator(*args, **kwargs) -> AsyncGenerator[list[T]]:
        async for page in _async_generator(items):
            yield page

    return _generator


def make_api_due(
    date: str,
    is_recurring: bool = False,
    string: str = "",
    timezone: str | None = None,
) -> Due:
    """Create a Due via from_dict to mirror API deserialization."""
    data: dict = {
        "date": date,
        "is_recurring": is_recurring,
        "string": string,
    }
    if timezone is not None:
        data["timezone"] = timezone
    return Due.from_dict(data)


def make_api_task(
    id: str | None = None,
    content: str | None = None,
    completed_at: str | None = None,
    due: Due | None = None,
    project_id: str | None = None,
    description: str | None = None,
    parent_id: str | None = None,
) -> Task:
    """Build a todoist Task instance."""
    return Task(
        assignee_id="1",
        assigner_id="1",
        completed_at=completed_at,
        content=content or SUMMARY,
        created_at="2021-10-01T00:00:00",
        creator_id="1",
        description=description or "",
        due=due,
        id=id or "1",
        labels=["Label1"],
        order=1,
        parent_id=parent_id,
        priority=1,
        project_id=project_id or PROJECT_ID,
        section_id=None,
        duration=None,
        deadline=None,
        is_collapsed=False,
        updated_at="2021-10-01T00:00:00",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.todoist.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_due() -> Due:
    """Mock a fixed Due date matching frozen test time."""
    return make_api_due(date="2024-05-24", string="today")


@fixture
def mock_tasks(due: Due = Depends(mock_due)) -> list[Task]:
    """Mock a list of todoist Tasks."""
    return [make_api_task(due=due)]


@fixture
def mock_api_status() -> HTTPStatus | None:
    """Inject an http status error."""
    return None


@fixture
def mock_api(
    tasks: list[Task] = Depends(mock_tasks),
    status: HTTPStatus | None = Depends(mock_api_status),
) -> AsyncMock:
    """Mock the api state."""
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
    if status:
        response = Response()
        response.status_code = status
        api.get_tasks.side_effect = HTTPError(response=response)
    return api


@fixture
def mock_todoist_config_entry() -> MockConfigEntry:
    """Mock todoist configuration."""
    return MockConfigEntry(domain=DOMAIN, unique_id=TOKEN, data={CONF_TOKEN: TOKEN})


@fixture
def patch_api(api: AsyncMock = Depends(mock_api)) -> Generator[AsyncMock]:
    """Patch TodoistAPIAsync used by the config flow."""
    with patch(
        "homeassistant.components.todoist.config_flow.TodoistAPIAsync", return_value=api
    ):
        yield api
