"""Tryke skip stub (pending port)."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import button
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import mock_config_entry, mock_opengarage

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

_FAKE_TRANSLATIONS = {
    "component.button.entity_component.restart.name": "Restart",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def buttons(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_opengarage: MagicMock = Depends(mock_opengarage),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test standard OpenGarage buttons."""
    mock_config_entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entry = entity_registry.async_get("button.abcdef_restart")
    expect(entry is not None).to_be(True)
    expect(entry.unique_id).to_equal("12345_restart")
    await hass.services.async_call(
        button.DOMAIN,
        button.SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.abcdef_restart"},
        blocking=True,
    )
    expect(len(mock_opengarage.reboot.mock_calls)).to_equal(1)

    expect(bool(entry.device_id)).to_be(True)
    device_entry = device_registry.async_get(entry.device_id)
    expect(device_entry is not None).to_be(True)


_ = (mock_config_entry, mock_opengarage)
