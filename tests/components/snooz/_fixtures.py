"""Tryke fixtures for snooz tests (ported from conftest.py)."""

from tryke import Depends, fixture

from homeassistant.components.snooz.const import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import SnoozFixture, create_mock_snooz, create_mock_snooz_config_entry

from tests.hass_fixtures import (
    enable_bluetooth,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
)


@fixture
async def mock_connected_snooz(
    hass: HomeAssistant = Depends(hass_fixture),
    _bluetooth: None = Depends(enable_bluetooth),
) -> SnoozFixture:
    """Mock a Snooz configuration entry and device."""
    device = await create_mock_snooz()
    entry = await create_mock_snooz_config_entry(hass, device)
    return SnoozFixture(entry, device)


@fixture
async def snooz_fan_entity_id(
    mock_connected_snooz: SnoozFixture = Depends(mock_connected_snooz),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> str:
    """Resolve the fan entity id for the mocked Snooz device."""
    return entity_registry.async_get_entity_id(
        Platform.FAN, DOMAIN, mock_connected_snooz.device.address
    )
