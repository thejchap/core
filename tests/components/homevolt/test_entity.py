"""Tests for the Homevolt entity."""

from unittest.mock import MagicMock

from homevolt import DeviceMetadata
from tryke import Depends, expect, fixture, test

from homeassistant.components.homevolt.const import DOMAIN, MANUFACTURER
from homeassistant.components.homevolt.switch import HomevoltLocalModeSwitch
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network

DEVICE_IDENTIFIER = "ems_40580137858664"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def homevolt_entity_device_info_with_metadata(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HomevoltEntity device info when device_metadata is present."""
    coordinator = MagicMock()
    coordinator.data.unique_id = "40580137858664"
    coordinator.data.device_metadata = {
        DEVICE_IDENTIFIER: DeviceMetadata(name="Homevolt EMS", model="EMS-1000"),
    }
    coordinator.client.base_url = "http://127.0.0.1"

    entity = HomevoltLocalModeSwitch(coordinator)
    expect(entity.device_info).not_.to_be(None)
    expect(entity.device_info["identifiers"]).to_equal(
        {(DOMAIN, f"40580137858664_{DEVICE_IDENTIFIER}")}
    )
    expect(entity.device_info["configuration_url"]).to_equal("http://127.0.0.1")
    expect(entity.device_info["manufacturer"]).to_equal(MANUFACTURER)
    expect(entity.device_info["model"]).to_equal("EMS-1000")
    expect(entity.device_info["name"]).to_equal("Homevolt EMS")


@test
async def homevolt_entity_device_info_without_metadata(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HomevoltEntity device info when device_metadata has no entry for device."""
    coordinator = MagicMock()
    coordinator.data.unique_id = "40580137858664"
    coordinator.data.device_metadata = {}
    coordinator.client.base_url = "http://127.0.0.1"

    entity = HomevoltLocalModeSwitch(coordinator)
    expect(entity.device_info).not_.to_be(None)
    expect(entity.device_info["identifiers"]).to_equal(
        {(DOMAIN, f"40580137858664_{DEVICE_IDENTIFIER}")}
    )
    expect(entity.device_info["manufacturer"]).to_equal(MANUFACTURER)
    expect(entity.device_info["model"]).to_be(None)
    expect(entity.device_info["name"]).to_be(None)
