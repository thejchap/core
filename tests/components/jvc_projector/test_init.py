"""Tests for JVC Projector config entry."""

from unittest.mock import AsyncMock, MagicMock, patch

from jvcprojector import JvcProjectorAuthError, JvcProjectorTimeoutError
from tryke import Depends, expect, fixture, test

from homeassistant.components.jvc_projector.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.issue_registry import IssueRegistry

from . import MOCK_MAC
from ._fixtures import mock_config_entry, mock_device, mock_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force a HookExecutor for this module."""


@test
async def init(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mock_device: MagicMock = Depends(mock_device),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test initialization."""
    mac = format_mac(MOCK_MAC)
    device = device_registry.async_get_device(identifiers={(DOMAIN, mac)})
    expect(device is not None).to_be(True)
    assert device is not None  # for type narrowing
    expect(device.identifiers).to_equal({(DOMAIN, mac)})


@test
async def unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: MagicMock = Depends(mock_device),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test config entry loading and unloading."""
    expect(mock_integration.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_integration.entry_id)
    await hass.async_block_till_done()


@test
async def disconnect_on_hass_stop(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: MagicMock = Depends(mock_device),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test device disconnects when Home Assistant stops."""
    expect(mock_integration.state).to_be(ConfigEntryState.LOADED)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()


@test
async def config_entry_connect_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: MagicMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config entry with connect error."""
    with patch(
        "homeassistant.components.jvc_projector.JvcProjector",
        autospec=True,
    ) as setup_mock:
        setup_mock.return_value.connect = AsyncMock(side_effect=JvcProjectorTimeoutError)
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def config_entry_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: MagicMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config entry with auth error."""
    with patch(
        "homeassistant.components.jvc_projector.JvcProjector",
        autospec=True,
    ) as setup_mock:
        setup_mock.return_value.connect = AsyncMock(side_effect=JvcProjectorAuthError)
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def deprecated_sensor_issue_lifecycle(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: IssueRegistry = Depends(issue_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_integration: MockConfigEntry = Depends(mock_integration),
) -> None:
    """Test deprecated sensor cleanup and issue lifecycle."""
    sensor_unique_id = f"{format_mac(MOCK_MAC)}_hdr_processing"
    issue_id = f"deprecated_sensor_{mock_integration.entry_id}_hdr_processing"

    expect(
        entity_registry.async_get_entity_id(Platform.SENSOR, DOMAIN, sensor_unique_id)
        is None
    ).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, issue_id) is None).to_be(True)

    sensor_entry = entity_registry.async_get_or_create(
        Platform.SENSOR,
        DOMAIN,
        sensor_unique_id,
        config_entry=mock_integration,
        suggested_object_id="jvc_projector_hdr_processing",
        disabled_by=er.RegistryEntryDisabler.INTEGRATION,
    )
    entity_id = sensor_entry.entity_id

    with patch(
        "homeassistant.components.jvc_projector.util.get_automations_and_scripts_using_entity",
        return_value=["- [Test Automation](/config/automation/edit/test_automation)"],
    ):
        await hass.config_entries.async_reload(mock_integration.entry_id)
        await hass.async_block_till_done()

    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    expect(issue is not None).to_be(True)
    assert issue is not None
    expect(issue.translation_key).to_equal("deprecated_sensor_scripts")
    expect(entity_registry.async_get(entity_id) is not None).to_be(True)

    await hass.config_entries.async_reload(mock_integration.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id) is None).to_be(True)
    expect(issue_registry.async_get_issue(DOMAIN, issue_id) is None).to_be(True)
