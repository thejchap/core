"""Tryke skip-stubs for test_bluetooth.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def bluetooth_coordinator_updates_based_on_websocket_state() -> None:
    """Stub for test_bluetooth_coordinator_updates_based_on_websocket_state."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def bt_offline_mode_entity_available_when_cloud_fails() -> None:
    """Stub for test_bt_offline_mode_entity_available_when_cloud_fails."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entity_without_bt_becomes_unavailable_when_cloud_fails_no_bt() -> None:
    """Stub for test_entity_without_bt_becomes_unavailable_when_cloud_fails_no_bt."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def bluetooth_coordinator_handles_connection_failure() -> None:
    """Stub for test_bluetooth_coordinator_handles_connection_failure."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def bluetooth_coordinator_triggers_entity_updates() -> None:
    """Stub for test_bluetooth_coordinator_triggers_entity_updates."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def setup_through_bluetooth_only() -> None:
    """Stub for test_setup_through_bluetooth_only."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def manual_offline_mode_no_bluetooth_device() -> None:
    """Stub for test_manual_offline_mode_no_bluetooth_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def manual_offline_mode() -> None:
    """Stub for test_manual_offline_mode."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def bluetooth_is_set_from_discovery() -> None:
    """Stub for test_bluetooth_is_set_from_discovery."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def disconnect_on_stop() -> None:
    """Stub for test_disconnect_on_stop."""
