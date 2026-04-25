"""Tryke fixtures for the Wyoming integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fx


@fixture
async def init_components(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up required components."""
    await async_setup_component(hass, "homeassistant", {})


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.wyoming.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
