"""Test the Motionblinds gateway helpers."""

from unittest.mock import Mock

from motionblinds import DEVICE_TYPES_WIFI, BlindType
from tryke import Depends, expect, fixture, test

from homeassistant.components.motion_blinds.gateway import device_name
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_BLIND_MAC = "abcdefghujkl0001"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture anchor."""


@test
async def device_name_helper(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Verify device_name returns expected names."""
    blind = Mock()
    blind.blind_type = BlindType.RollerBlind.name
    blind.mac = TEST_BLIND_MAC
    expect(device_name(blind)).to_equal("RollerBlind 0001")

    blind.device_type = DEVICE_TYPES_WIFI[0]
    expect(device_name(blind)).to_equal("RollerBlind")
