"""Test the Home Assistant Connect ZBT-2 config flow."""

from tryke import Depends, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires ZHA radio manager and homeassistant_hardware firmware mocking stack")
async def config_flow_zigbee(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Skipped homeassistant_connect_zbt2 tests need ZHA setup."""
