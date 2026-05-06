"""Tryke fixtures for the Model Context Protocol Server integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def ensure_homeassistant_loaded(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Ensure homeassistant component is loaded."""
    assert await async_setup_component(hass, "homeassistant", {})
    yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.mcp_server.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
