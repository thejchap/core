"""Tryke fixtures for Sonarr integration tests."""

from __future__ import annotations

import json
from collections.abc import Generator
from unittest.mock import MagicMock, patch

from aiopyarr import (
    Command,
    Diskspace,
    SonarrCalendar,
    SonarrEpisode,
    SonarrQueue,
    SonarrSeries,
    SonarrWantedMissing,
    SystemStatus,
)
from tryke import Depends, fixture

from homeassistant.components.sonarr.const import (
    CONF_BASE_PATH,
    CONF_UPCOMING_DAYS,
    CONF_WANTED_MAX_ITEMS,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_WANTED_MAX_ITEMS,
    DOMAIN,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture


def _sonarr_calendar() -> list[SonarrCalendar]:
    return [SonarrCalendar(r) for r in json.loads(load_fixture("sonarr/calendar.json"))]


def _sonarr_commands() -> list[Command]:
    return [Command(r) for r in json.loads(load_fixture("sonarr/command.json"))]


def _sonarr_diskspace() -> list[Diskspace]:
    return [Diskspace(r) for r in json.loads(load_fixture("sonarr/diskspace.json"))]


def _sonarr_queue() -> SonarrQueue:
    return SonarrQueue(json.loads(load_fixture("sonarr/queue.json")))


def _sonarr_series() -> list[SonarrSeries]:
    return [SonarrSeries(r) for r in json.loads(load_fixture("sonarr/series.json"))]


def _sonarr_system_status() -> SystemStatus:
    return SystemStatus(json.loads(load_fixture("sonarr/system-status.json")))


def _sonarr_wanted() -> SonarrWantedMissing:
    return SonarrWantedMissing(json.loads(load_fixture("sonarr/wanted-missing.json")))


def _sonarr_episodes() -> list[SonarrEpisode]:
    return [SonarrEpisode(r) for r in json.loads(load_fixture("sonarr/episodes.json"))]


def _apply_defaults(client: MagicMock) -> None:
    client.async_get_calendar.return_value = _sonarr_calendar()
    client.async_get_commands.return_value = _sonarr_commands()
    client.async_get_diskspace.return_value = _sonarr_diskspace()
    client.async_get_episodes.return_value = _sonarr_episodes()
    client.async_get_queue.return_value = _sonarr_queue()
    client.async_get_series.return_value = _sonarr_series()
    client.async_get_system_status.return_value = _sonarr_system_status()
    client.async_get_wanted.return_value = _sonarr_wanted()


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Sonarr",
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.189",
            CONF_PORT: 8989,
            CONF_BASE_PATH: "/api",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
            CONF_API_KEY: "MOCK_API_KEY",
            CONF_UPCOMING_DAYS: DEFAULT_UPCOMING_DAYS,
            CONF_WANTED_MAX_ITEMS: DEFAULT_WANTED_MAX_ITEMS,
        },
        options={
            CONF_UPCOMING_DAYS: DEFAULT_UPCOMING_DAYS,
            CONF_WANTED_MAX_ITEMS: DEFAULT_WANTED_MAX_ITEMS,
        },
        unique_id=None,
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.sonarr.async_setup_entry", return_value=True):
        yield


@fixture
def mock_sonarr_config_flow() -> Generator[MagicMock]:
    """Return a mocked Sonarr client for config_flow."""
    with patch(
        "homeassistant.components.sonarr.config_flow.SonarrClient", autospec=True
    ) as sonarr_mock:
        client = sonarr_mock.return_value
        _apply_defaults(client)
        yield client


@fixture
def mock_sonarr() -> Generator[MagicMock]:
    """Return a mocked Sonarr client."""
    with patch(
        "homeassistant.components.sonarr.SonarrClient", autospec=True
    ) as sonarr_mock:
        client = sonarr_mock.return_value
        _apply_defaults(client)
        yield client


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_sonarr),
) -> MockConfigEntry:
    """Set up the Sonarr integration for testing."""
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry
