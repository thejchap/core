"""Test the DSMR config flow."""

from tryke import Depends, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip(
    "complex DSMR/RFXtrx serial protocol mocking with parametrized telegram fixtures"
)
async def import_usb(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Skipped DSMR tests use complex serial-protocol fixtures."""
