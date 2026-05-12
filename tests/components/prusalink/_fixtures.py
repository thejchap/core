"""Tryke fixtures for PrusaLink tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.prusalink import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_version_api() -> Generator[dict[str, str]]:
    """Mock PrusaLink version API."""
    resp = {
        "api": "2.0.0",
        "server": "2.1.2",
        "text": "PrusaLink",
        "hostname": "PrusaXL",
        "firmware": "6.1.2+11023",
    }
    with patch("pyprusalink.PrusaLink.get_version", return_value=resp):
        yield resp


@fixture
def mock_info_api() -> Generator[dict[str, Any]]:
    """Mock PrusaLink info API."""
    resp = {
        "nozzle_diameter": 0.40,
        "mmu": False,
        "serial": "serial-1337",
        "hostname": "PrusaXL",
        "min_extrusion_temp": 170,
    }
    with patch("pyprusalink.PrusaLink.get_info", return_value=resp):
        yield resp


@fixture
def mock_get_legacy_printer() -> Generator[dict[str, Any]]:
    """Mock PrusaLink printer API."""
    resp = {"telemetry": {"material": "PLA"}}
    with patch("pyprusalink.PrusaLink.get_legacy_printer", return_value=resp):
        yield resp


@fixture
def mock_get_status_idle() -> Generator[dict[str, Any]]:
    """Mock PrusaLink printer status API (idle)."""
    resp = {
        "storage": {
            "path": "/usb/",
            "name": "usb",
            "read_only": False,
        },
        "printer": {
            "state": "IDLE",
            "temp_bed": 41.9,
            "target_bed": 60.5,
            "temp_nozzle": 47.8,
            "target_nozzle": 210.1,
            "axis_z": 1.8,
            "axis_x": 7.9,
            "axis_y": 8.4,
            "flow": 100,
            "speed": 100,
            "fan_hotend": 100,
            "fan_print": 75,
        },
    }
    with patch("pyprusalink.PrusaLink.get_status", return_value=resp):
        yield resp


@fixture
def mock_job_api_idle() -> Generator[dict[str, Any]]:
    """Mock PrusaLink job API having no job."""
    resp: dict[str, Any] = {}
    with patch("pyprusalink.PrusaLink.get_job", return_value=resp):
        yield resp


@fixture
def mock_api(
    mock_version_api: dict[str, str] = Depends(mock_version_api),
    mock_info_api: dict[str, Any] = Depends(mock_info_api),
    mock_get_legacy_printer: dict[str, Any] = Depends(mock_get_legacy_printer),
    mock_get_status_idle: dict[str, Any] = Depends(mock_get_status_idle),
    mock_job_api_idle: dict[str, Any] = Depends(mock_job_api_idle),
) -> None:
    """Mock PrusaLink API."""


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock a PrusaLink config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "http://example.com",
            "username": "dummy",
            "password": "dummypw",
        },
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry
