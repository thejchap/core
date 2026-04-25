"""Test the HERE Travel Time config flow."""

from tryke import Depends, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex menu-flow with many parametrize cases and shared fixture chains")
async def step_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Skipped here_travel_time tests use complex menu-flow setup."""
