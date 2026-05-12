"""Tests for JVC Projector sensor platform."""

from unittest.mock import MagicMock, patch

from jvcprojector import command as cmd
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import mock_config_entry, mock_device, mock_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

POWER_ID = "sensor.jvc_projector_status"
HDR_ENTITY_ID = "sensor.jvc_projector_hdr"


_FAKE_TRANSLATIONS = {
    "component.jvc_projector.entity.sensor.power.name": "Status",
    "component.jvc_projector.entity.sensor.hdr.name": "HDR",
    "component.jvc_projector.entity.sensor.hdr_processing.name": "HDR Processing",
    "component.jvc_projector.entity.sensor.color_depth.name": "Color Depth",
    "component.jvc_projector.entity.sensor.color_space.name": "Color Space",
    "component.jvc_projector.entity.sensor.light_time.name": "Light Time",
    "component.jvc_projector.entity.sensor.picture_mode.name": "Picture Mode",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _translations() -> None:
    """Inject translation slugs so per-entity translation_keys turn into _hdr etc."""
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
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _t: None = Depends(_translations),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def entity_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _device: MagicMock = Depends(mock_device),
    _integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Tests entity state is registered."""
    state = hass.states.get(POWER_ID)
    expect(state is not None).to_be(True)
    expect(entity_registry.async_get(state.entity_id) is not None).to_be(True)
    expect(state.state).to_equal("on")


@test
async def enable_hdr_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _device: MagicMock = Depends(mock_device),
    integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test enabling the HDR sensor (disabled by default)."""
    entry = entity_registry.async_get(HDR_ENTITY_ID)
    expect(entry is not None).to_be(True)
    expect(entry.disabled_by).to_be(er.RegistryEntryDisabler.INTEGRATION)

    entity_registry.async_update_entity(HDR_ENTITY_ID, disabled_by=None)
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(HDR_ENTITY_ID)
    expect(state is not None).to_be(True)


@test
async def unsupported_sensor_not_added(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device: MagicMock = Depends(mock_device),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test unsupported sensor descriptions are skipped."""
    device.supports.side_effect = lambda command: command is not cmd.ColorDepth

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(
        entity_registry.async_get("sensor.jvc_projector_color_depth") is None
    ).to_be(True)
