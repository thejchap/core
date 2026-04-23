"""Tryke fixtures for eafm."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.eafm.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def mock_get_stations() -> Generator[AsyncMock]:
    """Mock aioeafm.get_stations."""
    with patch("homeassistant.components.eafm.config_flow.get_stations") as patched:
        patched.return_value = [
            {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
        ]
        yield patched


@fixture
def initial_value() -> dict[str, Any]:
    """Mock aioeafm.get_station."""
    return {
        "label": "My station",
        "measures": [
            {
                "@id": "really-long-unique-id",
                "label": "York Viking Recorder - level-stage-i-15_min----",
                "qualifier": "Stage",
                "parameterName": "Water Level",
                "latestReading": {"value": 5},
                "stationReference": "L1234",
                "unit": "http://qudt.org/1.1/vocab/unit#Meter",
                "unitName": "m",
            }
        ],
    }


@fixture
def mock_get_station(
    initial_value: dict[str, Any] = Depends(initial_value),
) -> Generator[AsyncMock]:
    """Mock aioeafm.get_station."""
    with patch("homeassistant.components.eafm.coordinator.get_station") as patched:
        patched.return_value = initial_value
        yield patched


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass),
) -> MockConfigEntry:
    """Create a dummy config entry for testing."""
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        entry_id="VikingRecorder1234",
        data={"station": "L1234"},
        title="Viking Recorder",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
