"""Tryke fixtures for the Local Calendar integration."""

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from tryke import Depends, fixture

from homeassistant.components.local_calendar import LocalCalendarStore
from homeassistant.components.local_calendar.const import (
    CONF_CALENDAR_NAME,
    CONF_ICS_FILE,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, tmp_path as tmp_path_fixture

CALENDAR_NAME = "Light Schedule"
STORAGE_KEY = "light_schedule"


class FakeStore(LocalCalendarStore):
    """Mock storage implementation."""

    def __init__(
        self, hass: HomeAssistant, path: Path, ics_content: str, read_side_effect: Any
    ) -> None:
        """Initialize FakeStore."""
        super().__init__(hass, path)
        mock_path = self._mock_path = Mock()
        mock_path.exists = self._mock_exists
        mock_path.read_text = Mock()
        mock_path.read_text.return_value = ics_content
        mock_path.read_text.side_effect = read_side_effect
        mock_path.write_text = self._mock_write_text
        super().__init__(hass, mock_path)

    def _mock_exists(self) -> bool:
        return self._mock_path.read_text.return_value is not None

    def _mock_write_text(self, content: str) -> None:
        self._mock_path.read_text.return_value = content


@fixture
def mock_store() -> Generator[None]:
    """Patch the LocalCalendarStore implementation."""
    stores: dict[Path, FakeStore] = {}

    def new_store(hass: HomeAssistant, path: Path) -> FakeStore:
        if path not in stores:
            stores[path] = FakeStore(hass, path, "", None)
        return stores[path]

    with patch(
        "homeassistant.components.local_calendar.LocalCalendarStore", new=new_store
    ):
        yield


@fixture
async def set_time_zone(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set the time zone for the tests."""
    await hass.config.async_set_time_zone("America/Regina")


@fixture
def config_entry() -> MockConfigEntry:
    """Mock configuration entry."""
    return MockConfigEntry(domain=DOMAIN, data={CONF_CALENDAR_NAME: CALENDAR_NAME})


@fixture
async def setup_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    _store: None = Depends(mock_store),
    _tz: None = Depends(set_time_zone),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Set up the integration."""
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()


@fixture
def mock_ics_content() -> bytes:
    """Mock ics file content."""
    return b"""BEGIN:VCALENDAR
                VERSION:2.0
                PRODID:-//hacksw/handcal//NONSGML v1.0//EN
                END:VCALENDAR
            """


def _build_mock_process_uploaded_file(
    tmp_path: Path,
    ics_content: bytes,
) -> Generator[MagicMock]:
    """Build the upload mock with given ics content."""
    file_id_ics = str(uuid4())

    @contextmanager
    def _mock_process_uploaded_file(
        hass: HomeAssistant, uploaded_file_id: str
    ) -> Iterator[Path | None]:
        with open(tmp_path / uploaded_file_id, "wb") as icsfile:
            icsfile.write(ics_content)
        yield tmp_path / uploaded_file_id

    with (
        patch(
            "homeassistant.components.local_calendar.config_flow.process_uploaded_file",
            side_effect=_mock_process_uploaded_file,
        ) as mock_upload,
        patch(
            "shutil.move",
        ),
    ):
        mock_upload.file_id = {
            CONF_ICS_FILE: file_id_ics,
        }
        yield mock_upload


@fixture
def mock_process_uploaded_file(
    tmp_path: Path = Depends(tmp_path_fixture),
    ics_content: bytes = Depends(mock_ics_content),
) -> Generator[MagicMock]:
    """Mock upload ics file."""
    yield from _build_mock_process_uploaded_file(tmp_path, ics_content)


@fixture
def mock_process_uploaded_file_invalid(
    tmp_path: Path = Depends(tmp_path_fixture),
) -> Generator[MagicMock]:
    """Mock upload ics file with invalid content."""
    yield from _build_mock_process_uploaded_file(tmp_path, b"invalid-ics-content")
