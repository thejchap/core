"""Tryke fixtures for iotawatt tests (ported from conftest.py)."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.iotawatt.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Mock config entry added to HA."""
    entry = MockConfigEntry(
        domain=DOMAIN, title="Test Device", data={"host": "1.2.3.4"}
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_iotawatt(
    _entry: MockConfigEntry = Depends(entry),
) -> Generator[MagicMock]:
    """Mock iotawatt."""
    with patch("homeassistant.components.iotawatt.coordinator.Iotawatt") as mock:
        instance = mock.return_value
        instance.connect = AsyncMock(return_value=True)
        instance.update = AsyncMock()
        instance.getSensors.return_value = {"sensors": {}}
        yield instance
