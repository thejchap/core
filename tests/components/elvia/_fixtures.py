"""Tryke fixtures for the Elvia integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.elvia.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)
