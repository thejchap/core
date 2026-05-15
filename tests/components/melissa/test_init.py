"""The test for the Melissa Climate component."""

from unittest.mock import MagicMock

from tryke import Depends, fixture, test

from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_melissa

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    melissa: MagicMock = Depends(mock_melissa),
) -> None:
    """Test setting up the Melissa component."""
    await setup_integration(hass)

    melissa.assert_called_with(username="********", password="********")
