"""Test the Shelly config flow."""

from tryke import test


@test.skip("requires shelly_mock + websocket fixtures")
async def form() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_overrides_existing_discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_gen1_custom_port() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_errors_get_info() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_missing_model_key() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_missing_model_key_auth_enabled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_missing_model_key_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_errors_test_connection() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_setup_ignored_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_no_devices_discovered() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_with_zeroconf_devices() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_select_zeroconf_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_select_manual_entry() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_both_ble_and_zeroconf_prefers_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_with_ble_devices() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_filters_already_configured_devices() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_includes_ignored_devices() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_aborts_when_another_flow_finishes_while_in_progress() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_zeroconf_device_connection_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_zeroconf_device_validation_connection_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_zeroconf_device_requires_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_zeroconf_invalid_mac_filtered() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_zeroconf_no_ipv4_filtered() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_ble_device_without_rpc_over_ble_filtered() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_select_zeroconf_device_mac_mismatch() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_select_zeroconf_device_custom_port_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_select_zeroconf_device_not_fully_provisioned() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_select_ble_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def user_flow_filters_devices_with_active_discovery_flows() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_auth_errors_test_connection_gen1() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def form_auth_errors_test_connection_gen2() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_sleeping_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_sleeping_device_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_abort_setup_retry() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_abort_no_scripts_support() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_abort_zigbee_firmware() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_ignored() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_with_wifi_ap_ip() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_cannot_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_require_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def reauth_successful() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def reauth_unsuccessful() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def reauth_get_info_error() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_disabled_gen_1() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_enabled_gen_2() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_disabled_sleepy_gen_2() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def options_flow_ble() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_already_configured_triggers_refresh_mac_in_name() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_already_configured_triggers_refresh() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_sleeping_device_not_triggers_refresh() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_sleeping_device_attempts_configure() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_sleeping_device_attempts_configure_ws_disabled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_sleeping_device_attempts_configure_no_url_available() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def sleeping_device_gen2_with_new_firmware() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def reconfigure_successful() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def reconfigure_unsuccessful() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def reconfigure_with_exception() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_rejects_ipv6() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_wrong_device_name() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provisioning_clears_match_history() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_no_rpc_over_ble() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_factory_reset_rediscovery() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_invalid_name() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_mac_in_manufacturer_data() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_mac_unknown_model() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_already_configured_clears_match_history() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_discovery_no_ble_device() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_wifi_scan_success() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_wifi_scan_failure() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_wifi_scan_ble_not_permitted() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_wifi_credentials_and_provision_success() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_wifi_provision_failure() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_wifi_scan_unexpected_exception() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_unexpected_exception() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_device_connection_error_after_wifi() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_requires_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_validate_input_fails() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_firmware_not_fully_provisioned() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_with_zeroconf_discovery_fast_path() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_timeout_active_lookup_fails() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_timeout_ble_fallback_succeeds() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_timeout_ble_fallback_fails() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_timeout_ble_exception() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_secure_device_both_enabled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_secure_device_both_disabled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_secure_device_only_ap_disabled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_secure_device_only_ble_disabled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_secure_device_with_restart_required() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_secure_device_fails_gracefully() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def zeroconf_aborts_idle_ble_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_flow_abort_cleans_up_ble_connection() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_ble_initialize_failure_cleans_up() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_ble_shutdown_exception_handled() -> None:
    """Skipped pending fixture port."""

@test.skip("requires shelly_mock + websocket fixtures")
async def bluetooth_provision_ble_reconnect_fails_during_ip_fetch() -> None:
    """Skipped pending fixture port."""
