"""Test the Z-Wave JS Websocket API (tryke port).

The dev test_api.py is huge and most tests need either device_registry
fixtures, indirect platforms parametrize, or the supervisor-addon flow.
This port covers the simpler websocket commands that just need the deep
mock chain + hass_ws_client.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from zwave_js_server.const import ZwaveFeature

from homeassistant.components.zwave_js.api import (
    DSK,
    ENTRY_ID,
    ERR_NOT_LOADED,
    FEATURE,
    ID,
    QR_CODE_STRING,
    SECURITY_CLASSES,
    STATUS,
    TYPE,
)
from homeassistant.core import HomeAssistant

from ._fixtures import (
    client,
    integration,
    multisensor_6,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aiohttp_client,
    hass as hass_fixture,
    hass_access_token,
    hass_admin_credential,
    hass_admin_user,
    hass_owner_user,
    hass_ws_client,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture — see PATTERNS.md `_trigger_executor` note."""


# ---------------------------------------------------------------------------
# Simple websocket command tests.
# ---------------------------------------------------------------------------


@test("driver missing returns error from network_status")
async def no_driver(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    _multisensor: object = Depends(multisensor_6),
    integration: MockConfigEntry = Depends(integration),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test driver missing results in error."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    client.driver = None

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/network_status",
            ENTRY_ID: entry.entry_id,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)


@test("supports_feature websocket command")
async def supports_feature(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    integration: MockConfigEntry = Depends(integration),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test supports_feature websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"supported": True}

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/supports_feature",
            ENTRY_ID: entry.entry_id,
            FEATURE: ZwaveFeature.SMART_START,
        }
    )

    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal({"supported": True})


@test("cancel_inclusion_exclusion websocket command")
async def cancel_inclusion_exclusion(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    integration: MockConfigEntry = Depends(integration),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test cancelling the inclusion and exclusion process."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"success": True}

    await ws_client.send_json(
        {ID: 4, TYPE: "zwave_js/stop_inclusion", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    await ws_client.send_json(
        {ID: 5, TYPE: "zwave_js/stop_exclusion", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {ID: 8, TYPE: "zwave_js/stop_inclusion", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal(ERR_NOT_LOADED)

    await ws_client.send_json(
        {ID: 9, TYPE: "zwave_js/stop_exclusion", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal(ERR_NOT_LOADED)


@test("get_provisioning_entries websocket command")
async def get_provisioning_entries(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    integration: MockConfigEntry = Depends(integration),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test get_provisioning_entries websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {
        "entries": [{"dsk": "test", "securityClasses": [0], "fake": "test"}]
    }

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/get_provisioning_entries",
            ENTRY_ID: entry.entry_id,
        }
    )

    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        [{DSK: "test", SECURITY_CLASSES: [0], STATUS: 0, "fake": "test"}]
    )

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {ID: 7, TYPE: "zwave_js/get_provisioning_entries", ENTRY_ID: entry.entry_id}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal(ERR_NOT_LOADED)


@test("try_parse_dsk_from_qr_code_string websocket command")
async def try_parse_dsk_from_qr_code_string(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    integration: MockConfigEntry = Depends(integration),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client),
) -> None:
    """Test try_parse_dsk_from_qr_code_string websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    client.async_send_command.return_value = {"dsk": "a"}

    await ws_client.send_json(
        {
            ID: 1,
            TYPE: "zwave_js/try_parse_dsk_from_qr_code_string",
            ENTRY_ID: entry.entry_id,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )

    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal("a")

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 7,
            TYPE: "zwave_js/try_parse_dsk_from_qr_code_string",
            ENTRY_ID: entry.entry_id,
            QR_CODE_STRING: "90testtesttesttesttesttesttesttesttesttesttesttesttest",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal(ERR_NOT_LOADED)


# ---------------------------------------------------------------------------
# Skipped tests — require additional fixtures (device_registry, indirect
# parametrize, snapshot, etc).
# ---------------------------------------------------------------------------


@test.skip(
    "needs device_registry + Controller.async_get_state patching — port deferred"
)
async def network_status() -> None:
    """Stub for test_network_status."""


@test.skip("needs device_registry + Event replay — port deferred")
async def subscribe_node_status() -> None:
    """Stub for test_subscribe_node_status."""


@test.skip("needs device_registry + node device lookup — port deferred")
async def node_status() -> None:
    """Stub for test_node_status."""


@test.skip("needs device_registry + node device lookup — port deferred")
async def node_metadata() -> None:
    """Stub for test_node_metadata."""


@test.skip("needs device_registry + send_json_auto_id helper — port deferred")
async def node_alerts() -> None:
    """Stub for test_node_alerts."""


@test.skip("complex add_node flow with Event replay — port deferred")
async def add_node() -> None:
    """Stub for test_add_node."""


@test.skip("complex grant_security_classes flow — port deferred")
async def grant_security_classes() -> None:
    """Stub for test_grant_security_classes."""


@test.skip("validate_dsk_and_enter_pin Event-replay flow — port deferred")
async def validate_dsk_and_enter_pin() -> None:
    """Stub for test_validate_dsk_and_enter_pin."""


@test.skip("provision_smart_start_node — needs Provisioning model + Event replay")
async def provision_smart_start_node() -> None:
    """Stub for test_provision_smart_start_node."""


@test.skip("unprovision_smart_start_node — needs Provisioning model + Event replay")
async def unprovision_smart_start_node() -> None:
    """Stub for test_unprovision_smart_start_node."""


@test.skip("parse_qr_code_string requires QRProvisioningInformation roundtrip")
async def parse_qr_code_string() -> None:
    """Stub for test_parse_qr_code_string."""


@test.skip("remove_node — Event replay + device_registry — port deferred")
async def remove_node() -> None:
    """Stub for test_remove_node."""


@test.skip("replace_failed_node — complex Event replay — port deferred")
async def replace_failed_node() -> None:
    """Stub for test_replace_failed_node."""


@test.skip("remove_failed_node — Event replay + device_registry — port deferred")
async def remove_failed_node() -> None:
    """Stub for test_remove_failed_node."""


@test.skip("begin_rebuilding_routes — port deferred")
async def begin_rebuilding_routes() -> None:
    """Stub for test_begin_rebuilding_routes."""


@test.skip("subscribe_rebuild_routes_progress — Event replay — port deferred")
async def subscribe_rebuild_routes_progress() -> None:
    """Stub for test_subscribe_rebuild_routes_progress."""


@test.skip("subscribe_rebuild_routes_progress_initial_value — port deferred")
async def subscribe_rebuild_routes_progress_initial_value() -> None:
    """Stub for test_subscribe_rebuild_routes_progress_initial_value."""


@test.skip("stop_rebuilding_routes — port deferred")
async def stop_rebuilding_routes() -> None:
    """Stub for test_stop_rebuilding_routes."""


@test.skip("rebuild_node_routes — needs device_registry — port deferred")
async def rebuild_node_routes() -> None:
    """Stub for test_rebuild_node_routes."""


@test.skip("refresh_node_info — needs device_registry — port deferred")
async def refresh_node_info() -> None:
    """Stub for test_refresh_node_info."""


@test.skip("refresh_node_values — needs device_registry — port deferred")
async def refresh_node_values() -> None:
    """Stub for test_refresh_node_values."""


@test.skip("refresh_node_cc_values — needs device_registry — port deferred")
async def refresh_node_cc_values() -> None:
    """Stub for test_refresh_node_cc_values."""


@test.skip("set_config_parameter — port deferred (complex Value mock)")
async def set_config_parameter() -> None:
    """Stub for test_set_config_parameter."""


@test.skip("get_config_parameters — port deferred")
async def get_config_parameters() -> None:
    """Stub for test_get_config_parameters."""


@test.skip("set_raw_config_parameter — port deferred")
async def set_raw_config_parameter() -> None:
    """Stub for test_set_raw_config_parameter."""


@test.skip("get_raw_config_parameter — port deferred")
async def get_raw_config_parameter() -> None:
    """Stub for test_get_raw_config_parameter."""


@test.skip("subscribe_log_updates — Event replay — port deferred")
async def subscribe_log_updates() -> None:
    """Stub for test_subscribe_log_updates."""


@test.skip("update_log_config — port deferred")
async def update_log_config() -> None:
    """Stub for test_update_log_config."""


@test.skip("get_log_config — port deferred")
async def get_log_config() -> None:
    """Stub for test_get_log_config."""


@test.skip("data_collection — port deferred")
async def data_collection() -> None:
    """Stub for test_data_collection."""


@test.skip("abort_firmware_update — port deferred")
async def abort_firmware_update() -> None:
    """Stub for test_abort_firmware_update."""


@test.skip("is_node_firmware_update_in_progress — port deferred")
async def is_node_firmware_update_in_progress() -> None:
    """Stub for test_is_node_firmware_update_in_progress."""


@test.skip("subscribe_firmware_update_status — Event replay — port deferred")
async def subscribe_firmware_update_status() -> None:
    """Stub for test_subscribe_firmware_update_status."""


@test.skip("subscribe_firmware_update_status_initial_value — port deferred")
async def subscribe_firmware_update_status_initial_value() -> None:
    """Stub for test_subscribe_firmware_update_status_initial_value."""


@test.skip("get_node_firmware_update_capabilities — port deferred")
async def get_node_firmware_update_capabilities() -> None:
    """Stub for test_get_node_firmware_update_capabilities."""


@test.skip("is_any_ota_firmware_update_in_progress — port deferred")
async def is_any_ota_firmware_update_in_progress() -> None:
    """Stub for test_is_any_ota_firmware_update_in_progress."""


@test.skip("firmware_upload_view — needs HTTP client — port deferred")
async def firmware_upload_view() -> None:
    """Stub for test_firmware_upload_view."""


@test.skip("firmware_upload_view_failed_command — port deferred")
async def firmware_upload_view_failed_command() -> None:
    """Stub for test_firmware_upload_view_failed_command."""


@test.skip("firmware_upload_view_invalid_payload — port deferred")
async def firmware_upload_view_invalid_payload() -> None:
    """Stub for test_firmware_upload_view_invalid_payload."""


@test.skip("subscribe_controller_statistics — Event replay — port deferred")
async def subscribe_controller_statistics() -> None:
    """Stub for test_subscribe_controller_statistics."""


@test.skip("subscribe_node_statistics — Event replay — port deferred")
async def subscribe_node_statistics() -> None:
    """Stub for test_subscribe_node_statistics."""


@test.skip("hard_reset_controller — Event replay — port deferred")
async def hard_reset_controller() -> None:
    """Stub for test_hard_reset_controller."""


@test.skip("node_capabilities — needs device_registry — port deferred")
async def node_capabilities() -> None:
    """Stub for test_node_capabilities."""


@test.skip("invoke_cc_api — needs device_registry — port deferred")
async def invoke_cc_api() -> None:
    """Stub for test_invoke_cc_api."""


@test.skip("get_integration_settings — port deferred")
async def get_integration_settings() -> None:
    """Stub for test_get_integration_settings."""


@test.skip("backup_nvm — Event replay — port deferred")
async def backup_nvm() -> None:
    """Stub for test_backup_nvm."""


@test.skip("restore_nvm — Event replay — port deferred")
async def restore_nvm() -> None:
    """Stub for test_restore_nvm."""


@test.skip("subscribe_nvm_backup_progress — port deferred")
async def subscribe_nvm_backup_progress() -> None:
    """Stub for test_subscribe_nvm_backup_progress."""


@test.skip("cancel_secure_bootstrap_s2 — port deferred")
async def cancel_secure_bootstrap_s2() -> None:
    """Stub for test_cancel_secure_bootstrap_s2."""


@test.skip("subscribe_s2_inclusion — Event replay — port deferred")
async def subscribe_s2_inclusion() -> None:
    """Stub for test_subscribe_s2_inclusion."""


@test.skip("subscribe_new_devices — Event replay — port deferred")
async def subscribe_new_devices() -> None:
    """Stub for test_subscribe_new_devices."""


@test.skip("look_up_device — port deferred")
async def look_up_device() -> None:
    """Stub for test_look_up_device."""


@test.skip("ping_node — needs device_registry — port deferred")
async def ping_node() -> None:
    """Stub for test_ping_node."""


@test.skip("update_data_collection_preference — port deferred")
async def update_data_collection_preference() -> None:
    """Stub for test_update_data_collection_preference."""


@test.skip("set_default_log_levels — port deferred")
async def set_default_log_levels() -> None:
    """Stub for test_set_default_log_levels."""


@test.skip("get_log_config_full — port deferred")
async def get_log_config_full() -> None:
    """Stub for test_get_log_config_full."""


@test.skip("driver_firmware_upload_view — port deferred")
async def driver_firmware_upload_view() -> None:
    """Stub for test_driver_firmware_upload_view."""


@test.skip("driver_firmware_upload_view_failed_command — port deferred")
async def driver_firmware_upload_view_failed_command() -> None:
    """Stub for test_driver_firmware_upload_view_failed_command."""


@test.skip("driver_firmware_upload_view_invalid_payload — port deferred")
async def driver_firmware_upload_view_invalid_payload() -> None:
    """Stub for test_driver_firmware_upload_view_invalid_payload."""


@test.skip("driver_firmware_update_in_progress — port deferred")
async def driver_firmware_update_in_progress() -> None:
    """Stub for test_driver_firmware_update_in_progress."""


@test.skip("subscribe_node_status_no_device — port deferred")
async def subscribe_node_status_no_device() -> None:
    """Stub for test_subscribe_node_status_no_device."""


@test.skip("subscribe_inclusion_state — Event replay — port deferred")
async def subscribe_inclusion_state() -> None:
    """Stub for test_subscribe_inclusion_state."""


@test.skip("subscribe_state_event — Event replay — port deferred")
async def subscribe_state_event() -> None:
    """Stub for test_subscribe_state_event."""


@test.skip("get_value — port deferred")
async def get_value() -> None:
    """Stub for test_get_value."""


@test.skip("subscribe_validate_dsk — port deferred")
async def subscribe_validate_dsk() -> None:
    """Stub for test_subscribe_validate_dsk."""


@test.skip("hass_ws_api_get_state — port deferred")
async def hass_ws_api_get_state() -> None:
    """Stub for test_hass_ws_api_get_state."""


@test.skip("get_log_history — port deferred")
async def get_log_history() -> None:
    """Stub for test_get_log_history."""
