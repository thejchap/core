"""Tryke fixtures for PrusaLink tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_version_api() -> Generator[dict[str, str]]:
    """Mock PrusaLink version API."""
    resp = {
        "api": "2.0.0",
        "server": "2.1.2",
        "text": "PrusaLink",
        "hostname": "PrusaXL",
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
