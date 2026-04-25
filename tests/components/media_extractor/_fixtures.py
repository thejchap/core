"""Tryke fixtures for Media Extractor tests."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def setup_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Set up the homeassistant integration."""
    await async_setup_component(hass, "homeassistant", {})
    yield


@fixture
async def setup_media_player(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Set up the demo media player."""
    await async_setup_component(
        hass, "media_player", {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.media_extractor.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
