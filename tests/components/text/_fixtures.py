"""Tryke fixtures for the text integration tests."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


@fixture
def text_only() -> Generator[None]:
    """Enable only the text platform on the demo integration."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.TEXT],
    ):
        yield
