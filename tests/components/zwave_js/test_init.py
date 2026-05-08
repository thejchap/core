"""Tryke skip-stubs for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def entry_setup_unload() -> None:
    """Stub for test_entry_setup_unload."""


@test.skip("zwave_js: sibling test pending tryke port")
async def home_assistant_stop() -> None:
    """Stub for test_home_assistant_stop."""


@test.skip("zwave_js: sibling test pending tryke port")
async def initialized_timeout() -> None:
    """Stub for test_initialized_timeout."""


@test.skip("zwave_js: sibling test pending tryke port")
async def enabled_statistics() -> None:
    """Stub for test_enabled_statistics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def disabled_statistics() -> None:
    """Stub for test_disabled_statistics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def noop_statistics() -> None:
    """Stub for test_noop_statistics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def driver_ready_timeout_during_setup() -> None:
    """Stub for test_driver_ready_timeout_during_setup."""


@test.skip("zwave_js: sibling test pending tryke port")
async def listen_done_during_setup_before_forward_entry() -> None:
    """Stub for test_listen_done_during_setup_before_forward_entry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def not_connected_during_setup_after_forward_entry() -> None:
    """Stub for test_not_connected_during_setup_after_forward_entry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def listen_done_during_setup_after_forward_entry() -> None:
    """Stub for test_listen_done_during_setup_after_forward_entry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def listen_done_after_setup() -> None:
    """Stub for test_listen_done_after_setup."""


@test.skip("zwave_js: sibling test pending tryke port")
async def listen_ending_before_cancelling_listen() -> None:
    """Stub for test_listen_ending_before_cancelling_listen."""


@test.skip("zwave_js: sibling test pending tryke port")
async def listen_ending_unrecoverable_config_entry_state() -> None:
    """Stub for test_listen_ending_unrecoverable_config_entry_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def new_entity_on_value_added() -> None:
    """Stub for test_new_entity_on_value_added."""


@test.skip("zwave_js: sibling test pending tryke port")
async def on_node_added_ready() -> None:
    """Stub for test_on_node_added_ready."""


@test.skip("zwave_js: sibling test pending tryke port")
async def check_pre_provisioned_device_update_device() -> None:
    """Stub for test_check_pre_provisioned_device_update_device."""


@test.skip("zwave_js: sibling test pending tryke port")
async def check_pre_provisioned_device_remove_device() -> None:
    """Stub for test_check_pre_provisioned_device_remove_device."""


@test.skip("zwave_js: sibling test pending tryke port")
async def on_node_added_not_ready() -> None:
    """Stub for test_on_node_added_not_ready."""


@test.skip("zwave_js: sibling test pending tryke port")
async def existing_node_ready() -> None:
    """Stub for test_existing_node_ready."""


@test.skip("zwave_js: sibling test pending tryke port")
async def existing_node_reinterview() -> None:
    """Stub for test_existing_node_reinterview."""


@test.skip("zwave_js: sibling test pending tryke port")
async def existing_node_not_ready() -> None:
    """Stub for test_existing_node_not_ready."""


@test.skip("zwave_js: sibling test pending tryke port")
async def existing_node_not_replaced_when_not_ready() -> None:
    """Stub for test_existing_node_not_replaced_when_not_ready."""


@test.skip("zwave_js: sibling test pending tryke port")
async def null_name() -> None:
    """Stub for test_null_name."""


@test.skip("zwave_js: sibling test pending tryke port")
async def start_addon() -> None:
    """Stub for test_start_addon."""


@test.skip("zwave_js: sibling test pending tryke port")
async def start_addon_redacts_set_options_error() -> None:
    """Stub for test_start_addon_redacts_set_options_error."""


@test.skip("zwave_js: sibling test pending tryke port")
async def install_addon() -> None:
    """Stub for test_install_addon."""


@test.skip("zwave_js: sibling test pending tryke port")
async def addon_info_failure() -> None:
    """Stub for test_addon_info_failure."""


@test.skip("zwave_js: sibling test pending tryke port")
async def addon_options_changed() -> None:
    """Stub for test_addon_options_changed."""


@test.skip("zwave_js: sibling test pending tryke port")
async def update_addon() -> None:
    """Stub for test_update_addon."""


@test.skip("zwave_js: sibling test pending tryke port")
async def issue_registry() -> None:
    """Stub for test_issue_registry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def stop_addon() -> None:
    """Stub for test_stop_addon."""


@test.skip("zwave_js: sibling test pending tryke port")
async def remove_entry() -> None:
    """Stub for test_remove_entry."""


@test.skip("zwave_js: sibling test pending tryke port")
async def removed_device() -> None:
    """Stub for test_removed_device."""


@test.skip("zwave_js: sibling test pending tryke port")
async def suggested_area() -> None:
    """Stub for test_suggested_area."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_removed() -> None:
    """Stub for test_node_removed."""


@test.skip("zwave_js: sibling test pending tryke port")
async def replace_same_node() -> None:
    """Stub for test_replace_same_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def replace_different_node() -> None:
    """Stub for test_replace_different_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_model_change() -> None:
    """Stub for test_node_model_change."""


@test.skip("zwave_js: sibling test pending tryke port")
async def disabled_node_status_entity_on_node_replaced() -> None:
    """Stub for test_disabled_node_status_entity_on_node_replaced."""


@test.skip("zwave_js: sibling test pending tryke port")
async def remove_entity_on_value_removed() -> None:
    """Stub for test_remove_entity_on_value_removed."""


@test.skip("zwave_js: sibling test pending tryke port")
async def value_removed_and_readded() -> None:
    """Stub for test_value_removed_and_readded."""


@test.skip("zwave_js: sibling test pending tryke port")
async def value_never_populated_then_added() -> None:
    """Stub for test_value_never_populated_then_added."""


@test.skip("zwave_js: sibling test pending tryke port")
async def identify_event() -> None:
    """Stub for test_identify_event."""


@test.skip("zwave_js: sibling test pending tryke port")
async def server_logging() -> None:
    """Stub for test_server_logging."""


@test.skip("zwave_js: sibling test pending tryke port")
async def factory_reset_node() -> None:
    """Stub for test_factory_reset_node."""


@test.skip("zwave_js: sibling test pending tryke port")
async def entity_available_when_node_dead() -> None:
    """Stub for test_entity_available_when_node_dead."""


@test.skip("zwave_js: sibling test pending tryke port")
async def driver_ready_event() -> None:
    """Stub for test_driver_ready_event."""
