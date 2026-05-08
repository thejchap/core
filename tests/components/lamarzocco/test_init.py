"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def get_settings_errors() -> None:
    """Stub for test_get_settings_errors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def invalid_auth() -> None:
    """Stub for test_invalid_auth."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def v1_migration_fails() -> None:
    """Stub for test_v1_migration_fails."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def v4_migration() -> None:
    """Stub for test_v4_migration."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def migration_errors() -> None:
    """Stub for test_migration_errors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def config_flow_entry_migration_downgrade() -> None:
    """Stub for test_config_flow_entry_migration_downgrade."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def websocket_closed_on_unload() -> None:
    """Stub for test_websocket_closed_on_unload."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def gateway_version_issue() -> None:
    """Stub for test_gateway_version_issue."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device() -> None:
    """Stub for test_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def websocket_reconnects_after_termination() -> None:
    """Stub for test_websocket_reconnects_after_termination."""
