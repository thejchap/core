"""Tryke fixtures for the mqtt integration."""

from typing import Any

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_mqtt_mock


@fixture
def _module_marker() -> None:
    """Sentinel fixture to keep the module non-empty."""
    return None


@fixture
async def mqtt_mock(hass: HomeAssistant = Depends(hass_fixture)) -> Any:
    """Set up MQTT and return the mocked client.

    Mirrors the pytest ``mqtt_mock`` fixture from ``tests/conftest.py``.
    """
    return await setup_mqtt_mock(hass)
