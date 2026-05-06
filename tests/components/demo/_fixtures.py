"""Tryke fixtures for demo tests."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def setup_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the homeassistant integration."""
    await async_setup_component(hass, "homeassistant", {})


@fixture
def disable_platforms() -> Generator[None]:
    """Disable platforms to speed up tests."""
    with (
        patch(
            "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
            [],
        ),
        patch(
            "homeassistant.components.demo.COMPONENTS_WITH_DEMO_PLATFORM",
            [],
        ),
    ):
        yield
