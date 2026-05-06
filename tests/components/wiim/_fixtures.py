"""Tryke fixtures for the WiiM integration."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture
from wiim.models import WiimProbeResult

from homeassistant.components.wiim import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.wiim.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock Home Assistant ConfigEntry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        title="Test WiiM Device",
        unique_id="uuid:test-udn-1234",
    )


@fixture
def mock_probe_player() -> Generator[AsyncMock]:
    """Mock a WiimProbePlayer instance."""
    with patch(
        "homeassistant.components.wiim.config_flow.async_probe_wiim_device"
    ) as mock_probe:
        mock_probe.return_value = WiimProbeResult(
            host="192.168.1.100",
            udn="uuid:test-udn-1234",
            name="WiiM Pro",
            location="http://192.168.1.100:49152/description.xml",
            model="WiiM Pro",
        )
        yield mock_probe


@fixture
async def setup_internal_url(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Make sure internal url configured."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://192.168.1.10:8123"},
    )
