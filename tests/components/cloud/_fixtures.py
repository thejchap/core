"""Tryke fixtures for cloud tests."""

from collections.abc import AsyncGenerator

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def load_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Load the homeassistant integration.

    This is needed for the cloud integration to work.
    """
    assert await async_setup_component(hass, "homeassistant", {})
    yield
