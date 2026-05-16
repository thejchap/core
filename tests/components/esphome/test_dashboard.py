"""Test ESPHome dashboard features."""

from typing import Any
from unittest.mock import patch

from aioesphomeapi import APIClient, DeviceInfo, InvalidEncryptionKeyAPIError
from tryke import Depends, expect, fixture, test

from homeassistant.components.esphome import CONF_NOISE_PSK, DOMAIN, dashboard
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from . import VALID_NOISE_PSK
from ._fixtures import (
    MockESPHomeDeviceType,
    init_integration,
    load_homeassistant,
    mock_client,
    mock_config_entry,
    mock_dashboard,
    mock_esphome_device,
)
from .common import MockDashboardRefresh

from tests.common import MockConfigEntry
from tests.components.hassio._fixtures import hassio_stubs
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def dashboard_storage(
    hass: HomeAssistant = Depends(_trigger_executor),
    _dashboard: dict[str, Any] = Depends(mock_dashboard),
    _client: APIClient = Depends(mock_client),
    init_integration: MockConfigEntry = Depends(init_integration),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test dashboard storage."""
    expect(hass_storage[dashboard.STORAGE_KEY]["data"]).to_equal(
        {"info": {"addon_slug": "mock-slug", "host": "mock-host", "port": 1234}}
    )
    await dashboard.async_set_dashboard_info(hass, "test-slug", "new-host", 6052)
    expect(hass_storage[dashboard.STORAGE_KEY]["data"]).to_equal(
        {"info": {"addon_slug": "test-slug", "host": "new-host", "port": 6052}}
    )


@test
async def restore_dashboard_storage(
    hass: HomeAssistant = Depends(_trigger_executor),
    _homeassistant: None = Depends(load_homeassistant),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Restore dashboard url and slug from storage."""
    hass_storage[dashboard.STORAGE_KEY] = {
        "version": dashboard.STORAGE_VERSION,
        "minor_version": dashboard.STORAGE_VERSION,
        "key": dashboard.STORAGE_KEY,
        "data": {"info": {"addon_slug": "test-slug", "host": "new-host", "port": 6052}},
    }
    with patch.object(
        dashboard, "async_get_or_create_dashboard_manager"
    ) as mock_get_or_create:
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        expect(mock_get_or_create.call_count).to_equal(1)


@test
async def restore_dashboard_storage_end_to_end(
    hass: HomeAssistant = Depends(_trigger_executor),
    _homeassistant: None = Depends(load_homeassistant),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Restore dashboard url and slug from storage."""
    hass_storage[dashboard.STORAGE_KEY] = {
        "version": dashboard.STORAGE_VERSION,
        "minor_version": dashboard.STORAGE_VERSION,
        "key": dashboard.STORAGE_KEY,
        "data": {"info": {"addon_slug": "test-slug", "host": "new-host", "port": 6052}},
    }
    with (
        patch(
            "homeassistant.components.esphome.dashboard.is_hassio", return_value=False
        ),
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI"
        ) as mock_dashboard_api,
    ):
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        expect(mock_dashboard_api.mock_calls[0][1][0]).to_equal("http://new-host:6052")


@test
async def restore_dashboard_storage_skipped_if_addon_uninstalled(
    hass: HomeAssistant = Depends(_trigger_executor),
    _hassio: None = Depends(hassio_stubs),
    _homeassistant: None = Depends(load_homeassistant),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Restore dashboard restore is skipped if the addon is uninstalled."""
    hass_storage[dashboard.STORAGE_KEY] = {
        "version": dashboard.STORAGE_VERSION,
        "minor_version": dashboard.STORAGE_VERSION,
        "key": dashboard.STORAGE_KEY,
        "data": {"info": {"addon_slug": "test-slug", "host": "new-host", "port": 6052}},
    }
    with (
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI"
        ) as mock_dashboard_api,
        patch(
            "homeassistant.components.esphome.dashboard.is_hassio", return_value=True
        ),
        patch(
            "homeassistant.components.hassio.get_addons_info",
            return_value={},
        ),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()
        expect(mock_dashboard_api.called).to_be(False)


@test
async def setup_dashboard_fails(
    hass: HomeAssistant = Depends(_trigger_executor),
    _homeassistant: None = Depends(load_homeassistant),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test that nothing is stored on failed dashboard setup when there was no dashboard before."""
    with patch(
        "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_devices",
        side_effect=TimeoutError,
    ) as mock_get_devices:
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        await dashboard.async_set_dashboard_info(hass, "test-slug", "test-host", 6052)
        expect(mock_get_devices.call_count).to_equal(1)

    # The dashboard addon might recover later so we still
    # allow it to be set up.
    expect(dashboard.STORAGE_KEY in hass_storage).to_be(True)


@test
async def setup_dashboard_fails_when_already_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    _homeassistant: None = Depends(load_homeassistant),
    mock_client: APIClient = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test failed dashboard setup still reloads entries if one existed before."""
    with patch(
        "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_devices"
    ) as mock_get_devices:
        await dashboard.async_set_dashboard_info(
            hass, "test-slug", "working-host", 6052
        )
        await hass.async_block_till_done()

    expect(mock_get_devices.call_count).to_equal(1)
    expect(dashboard.STORAGE_KEY in hass_storage).to_be(True)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_devices",
            side_effect=TimeoutError,
        ) as mock_get_devices,
        patch(
            "homeassistant.components.esphome.async_setup_entry", return_value=True
        ) as mock_setup,
    ):
        await dashboard.async_set_dashboard_info(hass, "test-slug", "test-host", 6052)
        await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(mock_get_devices.call_count).to_equal(1)
    # We still setup, and reload, but we do not do the reauths
    expect(dashboard.STORAGE_KEY in hass_storage).to_be(True)
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def new_info_reload_config_entries(
    hass: HomeAssistant = Depends(_trigger_executor),
    _dashboard: dict[str, Any] = Depends(mock_dashboard),
    _client: APIClient = Depends(mock_client),
    init_integration: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test config entries are reloaded when new info is set."""
    expect(init_integration.state).to_be(ConfigEntryState.LOADED)

    with patch("homeassistant.components.esphome.async_setup_entry") as mock_setup:
        await dashboard.async_set_dashboard_info(hass, "test-slug", "test-host", 6052)

    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(mock_setup.mock_calls[0][1][1]).to_be(init_integration)

    # Test it's a no-op when the same info is set
    with patch("homeassistant.components.esphome.async_setup_entry") as mock_setup:
        await dashboard.async_set_dashboard_info(hass, "test-slug", "test-host", 6052)

    expect(len(mock_setup.mock_calls)).to_equal(0)


@test
async def new_dashboard_fix_reauth(
    hass: HomeAssistant = Depends(_trigger_executor),
    _homeassistant: None = Depends(load_homeassistant),
    mock_client: APIClient = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_dashboard: dict[str, Any] = Depends(mock_dashboard),
) -> None:
    """Test config entries waiting for reauth are triggered."""
    mock_client.device_info.side_effect = (
        InvalidEncryptionKeyAPIError("Wrong key", "test"),
        DeviceInfo(uses_password=False, name="test", mac_address="11:22:33:44:55:AA"),
    )

    with patch(
        "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_encryption_key",
        return_value=VALID_NOISE_PSK,
    ) as mock_get_encryption_key:
        result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(len(mock_get_encryption_key.mock_calls)).to_equal(0)

    mock_dashboard["configured"].append(
        {
            "name": "test",
            "configuration": "test.yaml",
        }
    )

    await MockDashboardRefresh(hass).async_refresh()

    with (
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.get_encryption_key",
            return_value=VALID_NOISE_PSK,
        ) as mock_get_encryption_key,
        patch(
            "homeassistant.components.esphome.async_setup_entry", return_value=True
        ) as mock_setup,
    ):
        await dashboard.async_set_dashboard_info(hass, "test-slug", "test-host", 6052)
        await hass.async_block_till_done()

    expect(len(mock_get_encryption_key.mock_calls)).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(mock_config_entry.data[CONF_NOISE_PSK]).to_equal(VALID_NOISE_PSK)


@test
async def dashboard_supports_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_dashboard: dict[str, Any] = Depends(mock_dashboard),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test dashboard supports update."""
    dash = dashboard.async_get_dashboard(hass)
    mock_refresh = MockDashboardRefresh(hass)

    entity_info = []
    states = []
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )

    # No data
    expect(bool(dash.supports_update)).to_be(False)

    await mock_refresh.async_refresh()
    expect(dash.supports_update).to_be(None)

    # supported version
    mock_dashboard["configured"].append(
        {
            "name": "test",
            "configuration": "test.yaml",
            "current_version": "2023.2.0-dev",
        }
    )

    await mock_refresh.async_refresh()
    expect(dash.supports_update).to_be(True)


@test
async def dashboard_unsupported_version(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_dashboard: dict[str, Any] = Depends(mock_dashboard),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test dashboard with unsupported version."""
    dash = dashboard.async_get_dashboard(hass)
    mock_refresh = MockDashboardRefresh(hass)

    entity_info = []
    states = []
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )

    # No data
    expect(bool(dash.supports_update)).to_be(False)

    await mock_refresh.async_refresh()
    expect(dash.supports_update).to_be(None)

    # unsupported version
    mock_dashboard["configured"].append(
        {
            "name": "test",
            "configuration": "test.yaml",
            "current_version": "2023.1.0",
        }
    )
    await mock_refresh.async_refresh()
    expect(dash.supports_update).to_be(False)
