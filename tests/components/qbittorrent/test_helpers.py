"""Test the qBittorrent helpers."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.qbittorrent.helpers import (
    format_progress,
    format_torrent,
    format_torrents,
    format_unix_timestamp,
    seconds_to_hhmmss,
)
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def seconds_to_hhmmss_(
    _trigger: None = Depends(_trigger_executor),
    _hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the seconds_to_hhmmss function."""
    expect(seconds_to_hhmmss(8640000)).to_equal("None")
    expect(seconds_to_hhmmss(3661)).to_equal("01:01:01")


@test
async def format_unix_timestamp_(
    _trigger: None = Depends(_trigger_executor),
    _hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the format_unix_timestamp function."""
    expect(format_unix_timestamp(1640995200)).to_equal("2022-01-01T00:00:00+00:00")


@test
async def format_progress_(
    _trigger: None = Depends(_trigger_executor),
    _hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the format_progress function."""
    expect(format_progress({"progress": 0.5})).to_equal("50.00")


@test
async def format_torrents_(
    _trigger: None = Depends(_trigger_executor),
    _hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the format_torrents function."""
    torrents_data = [
        {
            "name": "torrent1",
            "hash": "hash1",
            "added_on": 1640995200,
            "progress": 0.5,
            "state": "paused",
            "eta": 86400,
            "ratio": 1.0,
        },
        {
            "name": "torrent2",
            "hash": "hash1",
            "added_on": 1640995200,
            "progress": 0.5,
            "state": "paused",
            "eta": 86400,
            "ratio": 1.0,
        },
    ]

    expected_result = {
        "torrent1": {
            "id": "hash1",
            "added_date": "2022-01-01T00:00:00+00:00",
            "percent_done": "50.00",
            "status": "paused",
            "eta": "24:00:00",
            "ratio": "1.00",
        },
        "torrent2": {
            "id": "hash1",
            "added_date": "2022-01-01T00:00:00+00:00",
            "percent_done": "50.00",
            "status": "paused",
            "eta": "24:00:00",
            "ratio": "1.00",
        },
    }

    expect(format_torrents(torrents_data)).to_equal(expected_result)


@test
async def format_torrent_(
    _trigger: None = Depends(_trigger_executor),
    _hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the format_torrent function."""
    torrent_data = {
        "hash": "hash1",
        "added_on": 1640995200,
        "progress": 0.5,
        "state": "paused",
        "eta": 86400,
        "ratio": 1.0,
    }

    expected_result = {
        "id": "hash1",
        "added_date": "2022-01-01T00:00:00+00:00",
        "percent_done": "50.00",
        "status": "paused",
        "eta": "24:00:00",
        "ratio": "1.00",
    }

    expect(format_torrent(torrent_data)).to_equal(expected_result)
