"""Tryke skip-stubs for test_api.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def no_driver() -> None:
    """Stub for test_no_driver."""


@test.skip("zwave_js: sibling test pending tryke port")
async def network_status() -> None:
    """Stub for test_network_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_node_status() -> None:
    """Stub for test_subscribe_node_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_status() -> None:
    """Stub for test_node_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_metadata() -> None:
    """Stub for test_node_metadata."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_alerts() -> None:
    """Stub for test_node_alerts."""


@test.skip("zwave_js: sibling test pending tryke port")
async def add_node() -> None:
    """Stub for test_add_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def grant_security_classes() -> None:
    """Stub for test_grant_security_classes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def validate_dsk_and_enter_pin() -> None:
    """Stub for test_validate_dsk_and_enter_pin."""


@test.skip("zwave_js: sibling test pending tryke port")
async def provision_smart_start_node() -> None:
    """Stub for test_provision_smart_start_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unprovision_smart_start_node() -> None:
    """Stub for test_unprovision_smart_start_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_provisioning_entries() -> None:
    """Stub for test_get_provisioning_entries."""


@test.skip("zwave_js: sibling test pending tryke port")
async def parse_qr_code_string() -> None:
    """Stub for test_parse_qr_code_string."""


@test.skip("zwave_js: sibling test pending tryke port")
async def try_parse_dsk_from_qr_code_string() -> None:
    """Stub for test_try_parse_dsk_from_qr_code_string."""


@test.skip("zwave_js: sibling test pending tryke port")
async def supports_feature() -> None:
    """Stub for test_supports_feature."""


@test.skip("zwave_js: sibling test pending tryke port")
async def cancel_inclusion_exclusion() -> None:
    """Stub for test_cancel_inclusion_exclusion."""


@test.skip("zwave_js: sibling test pending tryke port")
async def remove_node() -> None:
    """Stub for test_remove_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def replace_failed_node() -> None:
    """Stub for test_replace_failed_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def remove_failed_node() -> None:
    """Stub for test_remove_failed_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def begin_rebuilding_routes() -> None:
    """Stub for test_begin_rebuilding_routes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_rebuild_routes_progress() -> None:
    """Stub for test_subscribe_rebuild_routes_progress."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_rebuild_routes_progress_initial_value() -> None:
    """Stub for test_subscribe_rebuild_routes_progress_initial_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def stop_rebuilding_routes() -> None:
    """Stub for test_stop_rebuilding_routes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def rebuild_node_routes() -> None:
    """Stub for test_rebuild_node_routes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def refresh_node_info() -> None:
    """Stub for test_refresh_node_info."""


@test.skip("zwave_js: sibling test pending tryke port")
async def refresh_node_values() -> None:
    """Stub for test_refresh_node_values."""


@test.skip("zwave_js: sibling test pending tryke port")
async def refresh_node_cc_values() -> None:
    """Stub for test_refresh_node_cc_values."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_config_parameter() -> None:
    """Stub for test_set_config_parameter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_config_parameters() -> None:
    """Stub for test_get_config_parameters."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_raw_config_parameter() -> None:
    """Stub for test_set_raw_config_parameter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_raw_config_parameter() -> None:
    """Stub for test_get_raw_config_parameter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def firmware_upload_view() -> None:
    """Stub for test_firmware_upload_view."""


@test.skip("zwave_js: sibling test pending tryke port")
async def firmware_upload_view_controller() -> None:
    """Stub for test_firmware_upload_view_controller."""


@test.skip("zwave_js: sibling test pending tryke port")
async def firmware_upload_view_failed_command() -> None:
    """Stub for test_firmware_upload_view_failed_command."""


@test.skip("zwave_js: sibling test pending tryke port")
async def firmware_upload_view_invalid_payload() -> None:
    """Stub for test_firmware_upload_view_invalid_payload."""


@test.skip("zwave_js: sibling test pending tryke port")
async def firmware_upload_view_no_driver() -> None:
    """Stub for test_firmware_upload_view_no_driver."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_view_non_admin_user() -> None:
    """Stub for test_node_view_non_admin_user."""


@test.skip("zwave_js: sibling test pending tryke port")
async def view_unloaded_config_entry() -> None:
    """Stub for test_view_unloaded_config_entry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def view_invalid_device_id() -> None:
    """Stub for test_view_invalid_device_id."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_log_updates() -> None:
    """Stub for test_subscribe_log_updates."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_log_config() -> None:
    """Stub for test_update_log_config."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_log_config() -> None:
    """Stub for test_get_log_config."""


@test.skip("zwave_js: sibling test pending tryke port")
async def data_collection() -> None:
    """Stub for test_data_collection."""


@test.skip("zwave_js: sibling test pending tryke port")
async def abort_firmware_update() -> None:
    """Stub for test_abort_firmware_update."""


@test.skip("zwave_js: sibling test pending tryke port")
async def is_node_firmware_update_in_progress() -> None:
    """Stub for test_is_node_firmware_update_in_progress."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_firmware_update_status() -> None:
    """Stub for test_subscribe_firmware_update_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_firmware_update_status_initial_value() -> None:
    """Stub for test_subscribe_firmware_update_status_initial_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_controller_firmware_update_status() -> None:
    """Stub for test_subscribe_controller_firmware_update_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_controller_firmware_update_status_initial_value() -> None:
    """Stub for test_subscribe_controller_firmware_update_status_initial_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_firmware_update_status_failures() -> None:
    """Stub for test_subscribe_firmware_update_status_failures."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_node_firmware_update_capabilities() -> None:
    """Stub for test_get_node_firmware_update_capabilities."""


@test.skip("zwave_js: sibling test pending tryke port")
async def is_any_ota_firmware_update_in_progress() -> None:
    """Stub for test_is_any_ota_firmware_update_in_progress."""


@test.skip("zwave_js: sibling test pending tryke port")
async def check_for_config_updates() -> None:
    """Stub for test_check_for_config_updates."""


@test.skip("zwave_js: sibling test pending tryke port")
async def install_config_update() -> None:
    """Stub for test_install_config_update."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_controller_statistics() -> None:
    """Stub for test_subscribe_controller_statistics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_node_statistics() -> None:
    """Stub for test_subscribe_node_statistics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def hard_reset_controller() -> None:
    """Stub for test_hard_reset_controller."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_capabilities() -> None:
    """Stub for test_node_capabilities."""


@test.skip("zwave_js: sibling test pending tryke port")
async def invoke_cc_api() -> None:
    """Stub for test_invoke_cc_api."""


@test.skip("zwave_js: sibling test pending tryke port")
async def backup_nvm() -> None:
    """Stub for test_backup_nvm."""


@test.skip("zwave_js: sibling test pending tryke port")
async def restore_nvm() -> None:
    """Stub for test_restore_nvm."""


@test.skip("zwave_js: sibling test pending tryke port")
async def cancel_secure_bootstrap_s2() -> None:
    """Stub for test_cancel_secure_bootstrap_s2."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_s2_inclusion() -> None:
    """Stub for test_subscribe_s2_inclusion."""


@test.skip("zwave_js: sibling test pending tryke port")
async def lookup_device() -> None:
    """Stub for test_lookup_device."""


@test.skip("zwave_js: sibling test pending tryke port")
async def subscribe_new_devices() -> None:
    """Stub for test_subscribe_new_devices."""
