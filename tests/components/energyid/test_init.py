"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def successful_setup() -> None:
    """Stub for test_successful_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_fails_on_timeout() -> None:
    """Stub for test_setup_fails_on_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_fails_on_auth_error() -> None:
    """Stub for test_setup_fails_on_auth_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_fails_when_not_claimed() -> None:
    """Stub for test_setup_fails_when_not_claimed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_auth_error_401_triggers_reauth() -> None:
    """Stub for test_setup_auth_error_401_triggers_reauth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_auth_error_403_triggers_reauth() -> None:
    """Stub for test_setup_auth_error_403_triggers_reauth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_http_error_triggers_retry() -> None:
    """Stub for test_setup_http_error_triggers_retry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_network_error_triggers_retry() -> None:
    """Stub for test_setup_network_error_triggers_retry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_sends_data() -> None:
    """Stub for test_state_change_sends_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_handles_invalid_values() -> None:
    """Stub for test_state_change_handles_invalid_values."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_ignores_unavailable() -> None:
    """Stub for test_state_change_ignores_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_ignores_unknown() -> None:
    """Stub for test_state_change_ignores_unknown."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def listener_tracks_entity_rename() -> None:
    """Stub for test_listener_tracks_entity_rename."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def listener_tracks_entity_removal() -> None:
    """Stub for test_listener_tracks_entity_removal."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_not_in_state_machine_during_setup() -> None:
    """Stub for test_entity_not_in_state_machine_during_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_cleans_up_listeners() -> None:
    """Stub for test_unload_cleans_up_listeners."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_valid_subentries_setup() -> None:
    """Stub for test_no_valid_subentries_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subentry_with_missing_uuid() -> None:
    """Stub for test_subentry_with_missing_uuid."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subentry_with_nonexistent_entity() -> None:
    """Stub for test_subentry_with_nonexistent_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def initial_state_queued_for_new_mapping() -> None:
    """Stub for test_initial_state_queued_for_new_mapping."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def synchronize_sensors_error_handling() -> None:
    """Stub for test_synchronize_sensors_error_handling."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_timeout_during_authentication() -> None:
    """Stub for test_setup_timeout_during_authentication."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def periodic_sync_error_and_recovery() -> None:
    """Stub for test_periodic_sync_error_and_recovery."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def periodic_sync_runtime_error() -> None:
    """Stub for test_periodic_sync_runtime_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_update_listener() -> None:
    """Stub for test_config_entry_update_listener."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def initial_state_non_numeric() -> None:
    """Stub for test_initial_state_non_numeric."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_during_entry_unload() -> None:
    """Stub for test_state_change_during_entry_unload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def late_appearing_entity_missing_data() -> None:
    """Stub for test_late_appearing_entity_missing_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_for_untracked_entity() -> None:
    """Stub for test_state_change_for_untracked_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry_with_subentries() -> None:
    """Stub for test_unload_entry_with_subentries."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry_client_close_error() -> None:
    """Stub for test_unload_entry_client_close_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry_unexpected_exception() -> None:
    """Stub for test_unload_entry_unexpected_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_update_listener_called() -> None:
    """Stub for test_config_entry_update_listener_called."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def initial_state_conversion_error_valueerror() -> None:
    """Stub for test_initial_state_conversion_error_valueerror."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_untracked_entity_explicit() -> None:
    """Stub for test_state_change_untracked_entity_explicit."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subentry_missing_keys_continue() -> None:
    """Stub for test_subentry_missing_keys_continue."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_unloading_flag_state_change() -> None:
    """Stub for test_entry_unloading_flag_state_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_subentries_explicit() -> None:
    """Stub for test_unload_subentries_explicit."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def initial_state_conversion_error() -> None:
    """Stub for test_initial_state_conversion_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change_after_entry_unloaded() -> None:
    """Stub for test_state_change_after_entry_unloaded."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def direct_state_change_handler() -> None:
    """Stub for test_direct_state_change_handler."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def subentry_unload_during_entry_unload() -> None:
    """Stub for test_subentry_unload_during_entry_unload."""

