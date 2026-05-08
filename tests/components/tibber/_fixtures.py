"""Tryke fixtures for the Tibber integration."""

from collections.abc import AsyncGenerator

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[object]:
    """Set up an in-memory recorder for tibber flow tests."""
    instance = await setup_recorder_mock(hass)
    yield instance
